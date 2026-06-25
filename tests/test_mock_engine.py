from app.core.mock_engine import MockEngine

def test_mock_engine_valid_report():
    engine = MockEngine()
    idea = "A new AI tutor for high school students"
    report = engine.analyze(idea)
    
    assert report.idea == idea
    assert report.engine == "mock"
    assert report.confidence == 0.55
    assert len(report.competitors) > 0
    assert len(report.opportunities) > 0
    assert len(report.gaps) > 0
    assert len(report.risks) > 0
    assert report.recommendation in ["build", "dont_build", "build_with_caveats"]

def test_mock_engine_determinism():
    engine1 = MockEngine()
    engine2 = MockEngine()
    
    idea = "A marketplace for freelance AI agents"
    
    report1 = engine1.analyze(idea)
    report2 = engine2.analyze(idea)
    
    assert report1.model_dump() == report2.model_dump()

def test_mock_engine_different_ideas_different_reports():
    engine = MockEngine()
    
    report1 = engine.analyze("A platform for selling digital art")
    report2 = engine.analyze("A smart home automation hub")
    
    assert report1.market_overview != report2.market_overview
    assert report1.reasoning != report2.reasoning or report1.recommendation != report2.recommendation or report1.competitors[0].name != report2.competitors[0].name
