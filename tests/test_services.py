import base64
import unittest

import httpx

from app.config import Settings
from app.schemas import Source
from app.services import AnswerGenerator, YandexSearchClient


class YandexSearchClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_decodes_and_parses_xml(self):
        xml = b"""<yandexsearch><response><results><grouping><group><doc>
          <url>https://example.com/page</url><title>Example &amp; test</title>
          <passages><passage>Useful search snippet</passage></passages>
        </doc></group></grouping></results></response></yandexsearch>"""

        async def handler(request):
            self.assertEqual(request.headers["Authorization"], "Api-Key secret")
            return httpx.Response(200, json={"rawData": base64.b64encode(xml).decode()})

        config = Settings(yandex_search_api_key="secret", yandex_folder_id="folder")
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result = await YandexSearchClient(config, client).search("query")

        self.assertEqual(result[0].title, "Example & test")
        self.assertEqual(result[0].domain, "example.com")
        self.assertEqual(result[0].snippet, "Useful search snippet")


class AnswerGeneratorTest(unittest.IsolatedAsyncioTestCase):
    async def test_uses_yandex_ai_studio_auth_and_model_uri(self):
        async def handler(request):
            self.assertEqual(request.headers["Authorization"], "Api-Key secret")
            self.assertEqual(request.url.path, "/v1/chat/completions")
            body = __import__("json").loads(request.content)
            self.assertEqual(body["model"], "gpt://folder/aliceai-llm-flash")
            return httpx.Response(
                200, json={"choices": [{"message": {"content": "Ответ [1]"}}]}
            )

        config = Settings(
            yandex_search_api_key="secret",
            yandex_folder_id="folder",
            llm_base_url="https://ai.api.cloud.yandex.net/v1",
            llm_model="gpt://{folder_id}/aliceai-llm-flash",
        )
        source = Source(
            id=1,
            title="Источник",
            url="https://example.com",
            domain="example.com",
            snippet="Факт",
        )
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            answer = await AnswerGenerator(config, client).generate("Вопрос", [source])

        self.assertEqual(answer, "Ответ [1]")
