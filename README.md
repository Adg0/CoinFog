# Unstoppable Mixer Algorand

## Motivation

https://www.reddit.com/r/AlgorandOfficial/comments/prs7b8/private_transactions_in_algorand/
![reddit post about anonymity](./docs/um_reddit.png)
![reddit response on post](./docs/um_reddit_resp.png)

Purchase with anonymity: to hide financial transaction

Medical expenses

Donations for charity

## Architecture

![Mixer idea drawing](./docs/Mixer_idea.jpg)

Depositor makes a deposit with app call to mixer contract. That is making a deposit of 5 Algos.

Withdrawal calls are made from a relay to preserve anonymity.
The relay is built as delegated contract; that is a smart signature.
A relay is used to break link to new account.

Safety is taken to protect relay delegation; that is

1. Rekey check
2. Fee check
3. Allows only application calls, specifically to mixer app
4. On completion is restricted to NoOp

### Depositing

Verify call sent is sent with 5 Algos, in atomic transction to pool.

Global state `next` is incremented

`Hash(secretX, nullfier)` is added to hash box

`MerkleProof(next)` is calculated

Global state `MerkelProof` is updated with MerkleProof(next) calculated value.

### Withdrawing

Password is sent as argument, example: `secretP, nullifier`.

Search nullifer box that no entry for `Hash(nullifierP)` is available.

Search hash box that their exsists `Hash(secretP)`

Update nullifier box by adding entry `Hash(nullifierP)`

Send Atomic transaction with:

```
Txn.account[0] gets 100k microAlgo: that is the relay fee, anyone can create another relay to collect relay fees
Txn.account[1] gets 5 Algo - relayFee - mixerFee
```

## ToDo

- [x] Relay
- [x] Relay test
- [x] Mixer contract
- [x] Mixer test
- [ ] Frontend wallet connect
- [ ] Documentation
- [ ] Presentation

