from pyteal import *

def approval_program():
    on_creation = Seq(
        [
            App.globalPut(Bytes("Creator"), Txn.sender()),
            App.globalPut(Bytes("MerkelRoot"), Sha256(Itob(Int(0)))),
            App.globalPut(Bytes("next"), Int(0)),
            App.globalPut(Bytes("profit"), Int(0)),
            Return(Int(1)),
        ]
    )

    is_creator = Txn.sender() == App.globalGet(Bytes("Creator"))

    """
    Deposit
        confirm 5Algo deposited
        add hash to '5algo' box
        calculate mekle root
        update global state
    """
    box_5algo_length = App.box_length(Bytes("5algo"))
    on_deposit = Seq(
            [
                # create box '5algo' if it doesn't exist
                box_5algo_length,
                If(Not(box_5algo_length.hasValue()), Assert(App.box_create(Bytes("5algo"), Int(992)))),
                Pop(App.box_create(Bytes("5algo"), Int(992))),
                # confim deposit
                Assert(
                    And(
                        Global.group_size() >= Int(2),
                        Gtxn[0].receiver() == Global.current_application_address(),
                        Gtxn[0].amount() == Int(5000000),
                    ),
                ),
                App.box_replace(Bytes("5algo"), App.globalGet(Bytes("next")) * Int(32), Txn.application_args[1]),
                App.globalPut(Bytes("next"), App.globalGet(Bytes("next")) + Int(1)),
                App.globalPut(Bytes("MerkelRoot"), Sha256(Concat(App.globalGet(Bytes("MerkelRoot")), Txn.application_args[1]))),
                Return(Int(1)),
            ]
    )

    """
    Withdrawing
        calculate hash(nf)
        search nullifier in 'NF' box
        calculate hash(secret,nf)
        search '5algo' box for existance
        update nullifier 'NF' box with insertion hash(nf)
        update profit
        innerTxn with atomic transaction:
            1) relayFee
            2) 5Algo - relayFee - mixerFee
    """
    relay_fee = Int(100000)
    mixer_fee = Int(100000)
    start = Int(0)
    i = ScratchVar(TealType.uint64)
    l = ScratchVar(TealType.uint64)
    nf_length = App.box_length(Bytes("NF"))
    opup = OpUp(OpUpMode.OnCall)
    on_withdraw = Seq(
            [
                nf_length,
                If(Not(nf_length.hasValue()), Assert(App.box_create(Bytes("NF"), Int(992)))),
                # loop
                l.store(nf_length.value()),
                # opcode budget extension
                opup.maximize_budget(Int(4800)),
                For(i.store(Int(0)), i.load() + Int(32) <= l.load(), i.store(i.load() + Int(1))).Do(
                    If(App.box_extract(Bytes("NF"), i.load(), Int(32)) == Global.zero_address()).Then(
                        App.box_replace(Bytes("NF"), i.load(), Sha256(Txn.application_args[2])),
                        Break()
                    ),
                    Assert(App.box_extract(Bytes("NF"), i.load(), Int(32)) != Sha256(Txn.application_args[2])),
                ),
                # end
                #Assert(App.box_extract(Bytes("5algo"), start, Int(32)) == Sha256(Concat(Txn.application_args[1], Txn.application_args[2]))),

                App.globalPut(Bytes("profit"), App.globalGet(Bytes("profit")) + Int(1)),
                # atomic transaction
                InnerTxnBuilder.Begin(),
                # relayFee
                InnerTxnBuilder.SetFields({
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.receiver: Txn.sender(),
                    TxnField.amount: relay_fee
                }),
                InnerTxnBuilder.Next(),
                # withdrawal
                InnerTxnBuilder.SetFields({
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.receiver: If(Txn.accounts.length() == Int(0), Txn.accounts[0], Txn.accounts[1]),
                    TxnField.amount: Int(5000000) - (relay_fee + mixer_fee)
                }),
                InnerTxnBuilder.Submit(),
                Return(Int(1)),
            ]
    )

    """
    Profit:
        check sender is creator
        build innerTxn to withdraw mixerFee collected
            Txn.sender() must cover innerTxn fees for taking profit
    """
    # calculate profit
    fees = Global.min_txn_fee() * Int(2) * App.globalGet(Bytes("profit"))
    gross_profit = mixer_fee * App.globalGet(Bytes("profit"))
    profits = gross_profit - fees
    on_profit = Seq(
            [
                # only creator takes profit
                Assert(is_creator),
                # update profit
                App.globalPut(Bytes("profit"), Int(0)),
                # send profits
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields({
                    TxnField.fee: Int(0),
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.amount: profits,
                    TxnField.receiver: App.globalGet(Bytes("Creator"))
                }),
                InnerTxnBuilder.Submit(),
                Return(Int(1)),
            ]
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(is_creator)],
        [Txn.application_args[0] == Bytes("deposit"), on_deposit],
        [Txn.application_args[0] == Bytes("withdraw"), on_withdraw],
        [Txn.application_args[0] == Bytes("profit"), on_profit],
    )

    return program

def clear_state_program():
    program = Seq(
        [
            Return(Int(1)),
        ]
    )

    return program


if __name__ == "__main__":
    with open("mixer_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), Mode.Application, version=8)
        f.write(compiled)

    with open("mixer_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), Mode.Application, version=8)
        f.write(compiled)
