import { BigInt } from "@graphprotocol/graph-ts"
import { Deposited, Withdrawn } from "../generated/StabilityVault/StabilityVault"
import { Account, Deposit, Withdrawal } from "../generated/schema"


export function handleDeposit(event: Deposited): void {
  let ownerId = event.params.user.toHex()
  let shares = event.params.shares

  if (ownerId == "0x0000000000000000000000000000000000000000") {
    return
  }

  // Load or create Account
  let account = Account.load(ownerId)
  if (account == null) {
    account = new Account(ownerId)
    account.balance = BigInt.fromI32(0)
    account.save()
  }

  // Update Account balance
  account.balance = account.balance.plus(shares)
  account.save()

  // Create Deposit entity
  let deposit = new Deposit(event.transaction.hash.toHex() + "-" + event.logIndex.toString())
  deposit.account = account.id
  deposit.amount = shares
  deposit.timestamp = event.block.timestamp
  deposit.transactionHash = event.transaction.hash
  deposit.save()
}


export function handleWithdraw(event: Withdrawn): void {
  let ownerId = event.params.user.toHex()
  let shares = event.params.shares

  if (ownerId == "0x0000000000000000000000000000000000000000") {
    return
  }

  // Load or create Account
  let account = Account.load(ownerId)
  if (account == null) {
    account = new Account(ownerId)
    account.balance = BigInt.fromI32(0)
    account.save()
  }

  // Update Account balance
  account.balance = account.balance.minus(shares)
  account.save()

  // Create Withdrawal entity
  let withdrawal = new Withdrawal(event.transaction.hash.toHex() + "-" + event.logIndex.toString())
  withdrawal.account = account.id
  withdrawal.amount = shares
  withdrawal.timestamp = event.block.timestamp
  withdrawal.transactionHash = event.transaction.hash
  withdrawal.save()
}
