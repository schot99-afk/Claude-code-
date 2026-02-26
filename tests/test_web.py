from budget_tool.web import create_app


def test_home_page_loads():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"budget_tool" in response.data
