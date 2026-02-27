from services.stock_resolver import resolve_stock

def test_resolve_stock_exact_ticker():
    assert set(resolve_stock("AAPL earnings")) == {"AAPL"}
    assert set(resolve_stock("MSFT Azure growth")) == {"MSFT"}
    assert set(resolve_stock("NVDA data center demand")) == {"NVDA"}

def test_resolve_stock_lowercase_ticker():
    assert set(resolve_stock("aapl guidance")) == {"AAPL"}

def test_resolve_stock_company_name():
    assert set(resolve_stock("Apple earnings")) == {"AAPL"}
    assert set(resolve_stock("microsoft earnings call")) == {"MSFT"}
    assert set(resolve_stock("nvidia stock")) == {"NVDA"}

def test_resolve_stock_multiple():
    # Should resolve both MSFT and AAPL
    resolved = resolve_stock("How does microsoft compare to apple inc?")
    assert set(resolved) == {"MSFT", "AAPL"}

def test_resolve_stock_no_false_positives():
    # 'pineapple' should NOT match 'apple' because of word boundaries
    assert resolve_stock("I like pineapple") == []
    # 'microsoftware' should not match 'microsoft'
    assert resolve_stock("microsoftware company") == []

def test_resolve_stock_none_found():
    assert resolve_stock("Why did tech stocks rise?") == []

if __name__ == "__main__":
    test_resolve_stock_exact_ticker()
    test_resolve_stock_lowercase_ticker()
    test_resolve_stock_company_name()
    test_resolve_stock_multiple()
    test_resolve_stock_no_false_positives()
    test_resolve_stock_none_found()
    print("All tests passed successfully!")
