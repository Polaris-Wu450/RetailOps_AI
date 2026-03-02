import os
import time
import anthropic
from celery import shared_task
from django.conf import settings
from .models import ActionPlan


def get_mock_action_plan(store_name, store_location, issue_description):
    """
    Mock LLM response for testing (no API call, no cost, instant)
    """
    return f"""**IMMEDIATE ACTIONS FOR {store_name}**

1. Emergency Response Team
   - Deploy on-site manager to {store_location} within 2 hours
   - Assess severity of: {issue_description}
   - Document current status with photos and incident report

2. Short-term Solution
   - Implement temporary workaround to minimize customer impact
   - Notify affected customers with expected resolution timeline
   - Set up alternative service if primary system unavailable

3. Root Cause Analysis
   - Schedule technical team inspection within 24 hours
   - Review maintenance logs and identify failure patterns
   - Prepare detailed incident report for management review

4. Communication Plan
   - Update store staff with talking points for customer inquiries
   - Post signage explaining situation and workarounds
   - Monitor social media and respond to complaints within 1 hour

5. Follow-up Actions
   - Schedule follow-up inspection in 7 days
   - Update preventive maintenance schedule
   - Train staff on early warning signs

**MOCK DATA - FOR TESTING ONLY**"""


def call_llm_api(store_name, store_location, issue_description):
    """
    Call real LLM API
    """
    client = anthropic.Anthropic(api_key=settings.RETAILOPS_API_KEY)
    
    prompt = f"""You are a retail operations assistant helping B2B managers. Generate a CONCISE, actionable plan for this store issue.

Store Name: {store_name}
Store Location: {store_location}
Issue: {issue_description}

Requirements:
- Provide 3-5 KEY ACTIONS only
- Each action must be SPECIFIC and IMMEDIATELY EXECUTABLE
- Focus on high-impact solutions
- Keep it brief - managers need to act quickly
- Format: Action title, 2-3 bullet points with concrete steps

Generate a short, practical action plan now:"""
    
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=False
)
def generate_action_plan(self, plan_id):
    """
    Celery task to generate action plan using LLM
    
    Features:
    - Automatic retry on failure (max 3 times)
    - Exponential backoff: 2s, 4s, 8s
    - Updates database status throughout process
    - Mock mode for testing (set USE_MOCK_LLM=true)
    """
    try:
        plan = ActionPlan.objects.get(id=plan_id)
        
        plan.status = 'processing'
        plan.save()
        
        use_mock = os.getenv('USE_MOCK_LLM', 'false').lower() == 'true'
        
        if use_mock:
            time.sleep(1)
            plan_content = get_mock_action_plan(
                plan.store_name, 
                plan.store_location, 
                plan.issue_description
            )
        else:
            plan_content = call_llm_api(
                plan.store_name,
                plan.store_location,
                plan.issue_description
            )
        
        plan.status = 'completed'
        plan.plan_content = plan_content
        plan.save()
        
        return {'status': 'completed', 'plan_id': plan_id, 'mock': use_mock}
        
    except ActionPlan.DoesNotExist:
        return {'status': 'error', 'message': f'ActionPlan {plan_id} not found'}
    
    except Exception as e:
        plan = ActionPlan.objects.get(id=plan_id)
        plan.status = 'failed'
        plan.error_message = str(e)
        plan.save()
        raise
