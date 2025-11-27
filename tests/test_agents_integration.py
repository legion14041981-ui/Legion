"""
Integration tests for Legion agents.

These tests verify that agents work correctly with real dependencies
and can perform end-to-end workflows.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from legion.agents import EmailAgent, GoogleSheetsAgent, DataAgent
from legion.agents.browser_agent import PlaywrightBrowserAgent
from legion.base_agent import LegionAgent


class TestEmailAgentIntegration:
    """Integration tests for EmailAgent."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_email_agent_smtp_mock(self):
        """Test EmailAgent with mocked SMTP."""
        agent = EmailAgent(
            agent_id="test_email",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="test@example.com",
            smtp_password="password",
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server

            result = await agent.send_email(
                to="recipient@example.com",
                subject="Test Email",
                body="This is a test",
            )

            assert result["success"] is True
            assert result["to"] == "recipient@example.com"
            mock_server.send_message.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_email_bulk_send(self):
        """Test bulk email sending with rate limiting."""
        agent = EmailAgent(
            agent_id="bulk_test",
            smtp_host="smtp.example.com",
        )

        recipients = [f"user{i}@example.com" for i in range(3)]

        with patch("smtplib.SMTP"):
            result = await agent.send_bulk(
                recipients=recipients,
                subject="Bulk Test",
                body="Test message",
                delay_seconds=0.01,  # Fast for testing
            )

            assert result["total"] == 3
            assert result["sent"] == 3
            assert result["failed"] == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_email_with_attachments(self):
        """Test email with file attachments."""
        agent = EmailAgent(agent_id="attach_test")

        # Create temporary test file
        test_file = Path("/tmp/test_attachment.txt")
        test_file.write_text("Test content")

        try:
            with patch("smtplib.SMTP") as mock_smtp:
                mock_server = MagicMock()
                mock_smtp.return_value = mock_server

                result = await agent.send_email(
                    to="test@example.com",
                    subject="With Attachment",
                    body="See attachment",
                    attachments=[str(test_file)],
                )

                assert result["success"] is True
                mock_server.send_message.assert_called_once()
        finally:
            test_file.unlink(missing_ok=True)


class TestDataAgentIntegration:
    """Integration tests for DataAgent."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_agent_json_pipeline(self):
        """Test complete JSON processing pipeline."""
        agent = DataAgent(
            agent_id="data_test",
            name="TestDataAgent",
            description="Test agent",
        )

        # Parse JSON
        json_data = '{"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}'
        parse_result = await agent.execute(
            {"capability": "data_parse_json", "data": json_data}
        )

        assert parse_result["success"] is True
        users = parse_result["result"]["users"]
        assert len(users) == 2

        # Filter data
        filter_result = await agent.execute(
            {
                "capability": "data_filter",
                "data": users,
                "options": {"filters": {"name": "Alice"}},
            }
        )

        assert filter_result["success"] is True
        assert len(filter_result["result"]) == 1
        assert filter_result["result"][0]["name"] == "Alice"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_agent_csv_processing(self):
        """Test CSV parsing and transformation."""
        agent = DataAgent(agent_id="csv_test", name="CSV Agent", description="CSV processor")

        csv_data = "name,age,city\nAlice,30,NYC\nBob,25,LA\nCharlie,35,SF"

        # Parse CSV
        parse_result = await agent.execute(
            {"capability": "data_parse_csv", "data": csv_data}
        )

        assert parse_result["success"] is True
        rows = parse_result["result"]
        assert len(rows) == 3
        assert rows[0]["name"] == "Alice"

        # Transform: select fields and limit
        transform_result = await agent.execute(
            {
                "capability": "data_transform",
                "data": rows,
                "options": {"fields": ["name", "city"], "limit": 2},
            }
        )

        assert len(transform_result["result"]) == 2
        assert "age" not in transform_result["result"][0]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_agent_aggregation(self):
        """Test data aggregation operations."""
        agent = DataAgent(agent_id="agg_test", name="AggAgent", description="Aggregator")

        data = [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20},
            {"category": "A", "value": 15},
            {"category": "B", "value": 25},
        ]

        # Aggregate by category with sum
        result = await agent.execute(
            {
                "capability": "data_aggregate",
                "data": data,
                "options": {"group_by": "category", "field": "value", "operation": "sum"},
            }
        )

        assert result["success"] is True
        assert result["result"]["A"] == 25
        assert result["result"]["B"] == 45

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_agent_validation(self):
        """Test data validation with schema."""
        agent = DataAgent(agent_id="val_test", name="ValidAgent", description="Validator")

        data = [{"name": "Alice", "age": "30"}, {"name": "Bob"}]  # Missing age

        result = await agent.execute(
            {
                "capability": "data_validate",
                "data": data,
                "options": {
                    "required_fields": ["name", "age"],
                    "schema": {"age": {"type": "int"}},
                },
            }
        )

        assert result["success"] is True
        validation = result["result"]
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0


class TestGoogleSheetsAgentIntegration:
    """Integration tests for GoogleSheetsAgent (mocked)."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sheets_agent_read_range(self):
        """Test reading from Google Sheets (mocked)."""
        agent = GoogleSheetsAgent(agent_id="sheets_test", name="SheetsAgent")

        # Mock the service
        agent.service = Mock()
        mock_values_api = Mock()
        agent.service.spreadsheets.return_value.values.return_value = mock_values_api
        mock_values_api.get.return_value.execute.return_value = {
            "values": [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]],
            "range": "Sheet1!A1:B3",
        }

        result = await agent.read_range(
            spreadsheet_id="test_id", range_name="Sheet1!A1:B3"
        )

        assert result["success"] is True
        assert result["rows"] == 3
        assert len(result["values"]) == 3

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sheets_agent_write_range(self):
        """Test writing to Google Sheets (mocked)."""
        agent = GoogleSheetsAgent(agent_id="sheets_write", name="WriterAgent")

        # Mock the service
        agent.service = Mock()
        mock_values_api = Mock()
        agent.service.spreadsheets.return_value.values.return_value = mock_values_api
        mock_values_api.update.return_value.execute.return_value = {
            "updatedCells": 6,
            "updatedRows": 3,
        }

        values = [["Name", "Age"], ["Alice", 30], ["Bob", 25]]
        result = await agent.write_range(
            spreadsheet_id="test_id", range_name="Sheet1!A1", values=values
        )

        assert result["success"] is True
        assert result["updatedCells"] == 6


class TestBrowserAgentIntegration:
    """Integration tests for PlaywrightBrowserAgent."""

    @pytest.mark.integration
    @pytest.mark.playwright
    @pytest.mark.asyncio
    async def test_browser_agent_lifecycle(self):
        """Test browser agent start/stop lifecycle."""
        agent = PlaywrightBrowserAgent(
            agent_id="browser_test", config={"headless": True, "browser": "chromium"}
        )

        await agent.start()
        assert agent.is_active is True
        assert agent.browser is not None
        assert agent.page is not None

        await agent.stop()
        assert agent.is_active is False
        assert agent.browser is None

    @pytest.mark.integration
    @pytest.mark.playwright
    @pytest.mark.asyncio
    async def test_browser_navigate_and_extract(self):
        """Test navigation and content extraction."""
        agent = PlaywrightBrowserAgent(
            agent_id="nav_test", config={"headless": True}
        )

        await agent.start()

        try:
            # Navigate to example.com
            nav_result = await agent.execute_async(
                {"action": "navigate", "params": {"url": "https://example.com"}}
            )

            assert nav_result["success"] is True
            assert "example.com" in nav_result["url"]

            # Extract page title
            extract_result = await agent.execute_async(
                {"action": "extract", "params": {"selector": "h1", "attribute": "textContent"}}
            )

            assert extract_result["success"] is True
            assert "Example" in extract_result["data"]
        finally:
            await agent.stop()


class TestAgentOrchestration:
    """Integration tests for multi-agent orchestration."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self):
        """Test workflow involving multiple agents."""
        # Create agents
        data_agent = DataAgent(agent_id="data", name="DataProcessor", description="Processor")
        email_agent = EmailAgent(agent_id="email", smtp_host="smtp.example.com")

        # Step 1: Process data
        csv_data = "name,email\nAlice,alice@example.com\nBob,bob@example.com"
        parse_result = await data_agent.execute(
            {"capability": "data_parse_csv", "data": csv_data}
        )

        assert parse_result["success"] is True
        users = parse_result["result"]

        # Step 2: Send emails (mocked)
        with patch("smtplib.SMTP"):
            for user in users:
                email_result = await email_agent.send_email(
                    to=user["email"],
                    subject="Welcome",
                    body=f"Hello {user['name']}",
                )
                assert email_result["success"] is True

        # Verify workflow
        assert data_agent.parse_count > 0
        assert email_agent.emails_sent == len(users)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
