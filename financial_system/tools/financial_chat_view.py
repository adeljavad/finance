from django.http import JsonResponse
from django.views import View

from ..tools import load_tools
from ..agents.financial_router import FinancialRouter
from ..agents.financial_agent import FinancialAgent

# ساخت اجزا یکبار در startup
TOOLS = load_tools()
ROUTER = FinancialRouter(TOOLS)
AGENT = FinancialAgent(ROUTER, TOOLS)


class FinancialChatView(View):

    async def post(self, request):
        body = json.loads(request.body)
        user_id = body.get("user_id", "guest")
        question = body.get("question", "")

        answer = await AGENT.ask(user_id, question)

        return JsonResponse({"answer": answer})
