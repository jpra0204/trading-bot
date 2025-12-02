import pytest

from trading_bot.brokers.base import BrokerError
from trading_bot.brokers.paper import PaperBrokerClient


def test_initialization():
    broker = PaperBrokerClient(starting_cash=50_000)
    assert broker.get_account_balance() == pytest.approx(50_000)
    assert broker.get_positions() == {}


def test_buy_flow():
    broker = PaperBrokerClient(starting_cash=100_000)
    broker.set_price("AAPL", 100.0)
    order = broker.place_order(symbol="AAPL", side="buy", quantity=10)

    assert order.status == "filled"
    assert broker.get_account_balance() == pytest.approx(99_000)
    position = broker.get_position("AAPL")
    assert position is not None
    assert position.quantity == pytest.approx(10)
    assert position.avg_price == pytest.approx(100.0)


def test_sell_flow():
    broker = PaperBrokerClient(starting_cash=100_000)
    broker.set_price("AAPL", 100.0)
    broker.place_order(symbol="AAPL", side="buy", quantity=10)
    broker.place_order(symbol="AAPL", side="sell", quantity=5)

    position = broker.get_position("AAPL")
    assert position is not None
    assert position.quantity == pytest.approx(5)
    assert broker.get_account_balance() == pytest.approx(99_500)


def test_error_when_price_missing():
    broker = PaperBrokerClient()
    with pytest.raises(BrokerError):
        broker.place_order(symbol="MSFT", side="buy", quantity=1)


@pytest.mark.parametrize("enable_short", [True])
def test_short_selling_behavior(enable_short: bool):  # noqa: ARG001
    broker = PaperBrokerClient(starting_cash=100_000)
    broker.set_price("AAPL", 100.0)
    broker.place_order(symbol="AAPL", side="sell", quantity=10)

    position = broker.get_position("AAPL")
    assert position is not None
    assert position.quantity == pytest.approx(-10)
    assert broker.get_account_balance() == pytest.approx(101_000)
