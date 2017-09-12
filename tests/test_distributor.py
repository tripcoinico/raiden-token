import pytest
from ethereum import tester
import math
from web3.utils.compat import (
    Timeout,
)
from utils import (
    handle_logs,
)
from fixtures import (
    auction_args,
    create_contract,
    auction_contract,
    get_token_contract,
    token_contract,
    print_logs,
    txnCost,
)

from auction_fixtures import (
    auction_setup_contract,
    auction_ended,
    auction_bid_tested,
    auction_end_tests,
    auction_claimed_tests,
)


@pytest.fixture()
def distributor_contract(chain, create_contract, auction_contract):
    Distributor = chain.provider.get_contract_factory('Distributor')
    distributor_contract = create_contract(Distributor, [auction_contract.address])

    print_logs(distributor_contract, 'Distributed', 'Distributor')
    print_logs(distributor_contract, 'ClaimTokensCalled', 'Distributor')

    return distributor_contract


def test_distributor_init(chain, web3, create_contract):
    A = web3.eth.accounts[2]
    Distributor = chain.provider.get_contract_factory('Distributor')
    Auction = chain.provider.get_contract_factory('DutchAuction')
    auction = create_contract(Auction, auction_args[0])
    other_owner_auction = create_contract(Auction, auction_args[0], {'from': A})

    # Fail if no auction address provided
    with pytest.raises(TypeError):
        distributor_contract = create_contract(Distributor, [])

    # Fail if auction has another owner
    with pytest.raises(tester.TransactionFailed):
        distributor_contract = create_contract(Distributor, [other_owner_auction.address])

    distributor_contract = create_contract(Distributor, [auction.address])


def claim_tokens(auction, distributor, addresses):
    get_bidders_addresses


def auction_post_claim_tokens_tests(token, auction, bidder, value, bidder_pre_balance, auction_pre_balance):
    # Check if bidder has the correct number of tokens
    bidder_balance = bidder_pre_balance + value
    auction_balance = auction_pre_balance + value
    assert token.call().balanceOf(bidder) == bidder_balance
    assert token.call().balanceOf(auction.address) == auction_balance

    # Bidder cannot claim tokens again
    with pytest.raises(tester.TransactionFailed):
        auction.transact({'from': bidder}).claimTokens()


def test_distributor_distribute(web3, token_contract, distributor_contract, auction_ended, auction_claimed_tests):
    distributor = distributor_contract
    token = token_contract
    auction = auction_ended
    addresses = []
    values = []
    claimed = []
    verified_claim = []

    # Retrieve bidder addresses from contract bid events
    def get_bidders_addresses(event):
        address = event['args']['_sender']

        if address not in addresses:
            addresses.append(address)
            values.append(0)
            index = len(addresses) - 1
        else:
            index = addresses.index(address)

        values[index] += event['args']['_amount']

    handle_logs(contract=auction, event='BidSubmission', callback=get_bidders_addresses)

    # Send 5 claiming transactions in a single batch to not run out of gas
    safe_distribution_no = 5
    steps = math.ceil(len(addresses) / safe_distribution_no)

    owner_pre_balance = web3.eth.getBalance(auction.call().owner())
    auction_pre_balance = web3.eth.getBalance(auction.address)

    # Call the distributor contract with batches of bidder addresses
    for i in range(0, steps):
        start = i * safe_distribution_no
        end = (i + 1) * safe_distribution_no
        distributor.transact({}).distribute(addresses[start : end])

    auction_claimed_tests(auction, owner_pre_balance, auction_pre_balance)

    # Verify that a single "ClaimedTokens" event has been issued by the auction contract
    # for each address
    for j in range(0, len(addresses) - 1):
        address = addresses[j]
        assert auction.call().bids(address) == 0

        def verify_claim(event):
            # Check for double claiming
            assert address not in verified_claim
            sent_amount = event['args']['_sent_amount']
            verified_claim.append(address)

            # TODO assert sent_amount == token balance

        # check if auction event was triggered for this user
        handle_logs(contract=auction,
            event='ClaimedTokens',
            params={
                'filter': {'_recipient': address}
            },
            callback=verify_claim)




def test_waitfor_last_events_timeout():
    with Timeout(20) as timeout:
        timeout.sleep(2)