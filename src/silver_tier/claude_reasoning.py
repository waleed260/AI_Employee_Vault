import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger("ClaudeReasoningEngine")


class ReasoningType(Enum):
    TASK_ANALYSIS = "task_analysis"
    DECISION_MAKING = "decision_making"
    PROBLEM_SOLVING = "problem_solving"
    PLANNING = "planning"
    RISK_ASSESSMENT = "risk_assessment"


class ClaudeReasoningEngine:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.reasoning_dir = self.vault_path / "Reasoning"
        self.reasoning_dir.mkdir(exist_ok=True)

        self.plans_dir = self.vault_path / "Plans"
        self.plans_dir.mkdir(exist_ok=True)

        logger.info("ClaudeReasoningEngine initialized - Silver Tier")

    def analyze_task(self, task_data: Dict) -> Dict:
        task_type = task_data.get("type", "general")
        priority = task_data.get("priority", "medium")
        context = task_data.get("context", "")

        analysis = {
            "task_id": task_data.get(
                "id", f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            ),
            "type": task_type,
            "priority": priority,
            "complexity": self._assess_complexity(task_data),
            "risks": self._identify_risks(task_data),
            "resources_needed": self._identify_resources(task_data),
            "dependencies": self._find_dependencies(task_data),
            "estimated_time": self._estimate_time(task_data),
            "steps": self._generate_steps(task_data),
            "reasoning": self._reason_about_task(task_data),
        }

        return analysis

    def _assess_complexity(self, task_data: Dict) -> str:
        complexity_score = 0

        if len(task_data.get("description", "")) > 200:
            complexity_score += 1
        if len(task_data.get("subtasks", [])) > 3:
            complexity_score += 1
        if "external" in str(task_data.get("tags", [])).lower():
            complexity_score += 1
        if "approval" in str(task_data.get("requires", [])).lower():
            complexity_score += 1

        if complexity_score <= 1:
            return "simple"
        elif complexity_score <= 3:
            return "moderate"
        else:
            return "complex"

    def _identify_risks(self, task_data: Dict) -> List[str]:
        risks = []

        task_type = task_data.get("type", "").lower()

        if "payment" in task_type or "financial" in task_type:
            risks.append("Financial risk - requires approval")
            risks.append("Data accuracy critical")

        if "email" in task_type or "communication" in task_type:
            risks.append("Message miscommunication")
            risks.append("Reply to wrong recipient")

        if "delete" in task_type or "remove" in task_type:
            risks.append("Data loss risk")
            risks.append("Irreversible action")

        if task_data.get("priority") == "high":
            risks.append("Time-sensitive - deadline pressure")

        if not task_data.get("context"):
            risks.append("Insufficient context - may need clarification")

        return risks

    def _identify_resources(self, task_data: Dict) -> List[str]:
        resources = []

        task_type = task_data.get("type", "").lower()

        if "email" in task_type:
            resources.append("Gmail service")
            resources.append("Email template library")

        if "payment" in task_type:
            resources.append("Payment service")
            resources.append("Approval workflow")

        if "linkedin" in task_type:
            resources.append("LinkedIn API")

        if "whatsapp" in task_type:
            resources.append("WhatsApp API")

        if "create" in task_type or "generate" in task_type:
            resources.append("AI text generation")

        if not resources:
            resources.append("Standard vault operations")

        return resources

    def _find_dependencies(self, task_data: Dict) -> List[str]:
        dependencies = []

        if "approval" in str(task_data.get("requires", [])).lower():
            dependencies.append("Requires human approval")

        if task_data.get("type") == "payment":
            dependencies.append("Budget verification needed")

        if task_data.get("priority") == "high":
            dependencies.append("Priority queue access")

        return dependencies

    def _estimate_time(self, task_data: Dict) -> str:
        complexity = self._assess_complexity(task_data)

        time_estimates = {
            "simple": "15-30 minutes",
            "moderate": "1-2 hours",
            "complex": "2-4 hours",
        }

        return time_estimates.get(complexity, "1-2 hours")

    def _generate_steps(self, task_data: Dict) -> List[str]:
        steps = []

        task_type = task_data.get("type", "").lower()

        if "email" in task_type:
            steps.append("Read and understand email content")
            steps.append("Draft response if needed")
            steps.append("Check if new contact - request approval if yes")
            steps.append("Send response or move to appropriate folder")

        elif "payment" in task_type:
            steps.append("Verify payment details")
            steps.append("Check budget/approval limits")
            steps.append("Move to Pending_Approval")
            steps.append("Execute after approval")

        elif "file" in task_type:
            steps.append("Analyze file content")
            steps.append("Determine appropriate action")
            steps.append("Execute action")

        else:
            steps.append("Analyze the task")
            steps.append("Determine required resources")
            steps.append("Execute the task")
            steps.append("Log results")

        return steps

    def _reason_about_task(self, task_data: Dict) -> str:
        reasoning_parts = []

        task_type = task_data.get("type", "general task")
        priority = task_data.get("priority", "medium")

        reasoning_parts.append(f"Analyzing {task_type} with {priority} priority.")

        complexity = self._assess_complexity(task_data)
        reasoning_parts.append(f"This is a {complexity} task.")

        risks = self._identify_risks(task_data)
        if risks:
            reasoning_parts.append(f"Key risks identified: {', '.join(risks[:2])}")

        if "approval" in str(task_data.get("requires", [])).lower():
            reasoning_parts.append("Approval workflow will be triggered.")

        return " ".join(reasoning_parts)

    def create_plan(self, task_data: Dict) -> Dict:
        analysis = self.analyze_task(task_data)

        plan_id = f"PLAN_{analysis['task_id']}_{datetime.now().strftime('%Y%m%d')}"

        plan_content = f"""---
type: plan
item: {task_data.get("id", "unknown")}
created: {datetime.now().isoformat()}
status: pending
priority: {task_data.get("priority", "medium")}
complexity: {analysis["complexity"]}
---

# Plan: {task_data.get("title", "Untitled Task")}

## Reasoning Analysis

**Complexity:** {analysis["complexity"]}
**Estimated Time:** {analysis["estimated_time"]}
**Type:** {analysis["type"]}

### Reasoning
{analysis["reasoning"]}

## Risk Assessment

"""

        for risk in analysis["risks"]:
            plan_content += f"- ⚠️ {risk}\n"

        plan_content += f"""
## Resources Needed

"""

        for resource in analysis["resources_needed"]:
            plan_content += f"- {resource}\n"

        plan_content += f"""
## Dependencies

"""

        if analysis["dependencies"]:
            for dep in analysis["dependencies"]:
                plan_content += f"- {dep}\n"
        else:
            plan_content += "- No dependencies\n"

        plan_content += f"""
## Execution Steps

"""

        for i, step in enumerate(analysis["steps"], 1):
            plan_content += f"- [ ] {i}. {step}\n"

        approval_required = (
            len(analysis["risks"]) > 0 or len(analysis["dependencies"]) > 0
        )

        plan_content += f"""
## Approval Required

{"Yes - Human approval recommended due to identified risks" if approval_required else "No - Can be executed automatically"}

## Task Details

**Original Type:** {task_data.get("type", "general")}
**Context:** {task_data.get("context", "Not provided")}

"""

        plan_file = self.plans_dir / f"{plan_id}.md"
        plan_file.write_text(plan_content)

        logger.info(f"Created plan: {plan_id}")

        return {
            "status": "success",
            "plan_id": plan_id,
            "plan_path": str(plan_file),
            "analysis": analysis,
            "approval_required": approval_required,
        }

    def review_and_update_plan(self, plan_path: str, execution_result: Dict) -> Dict:
        plan_file = Path(plan_path)

        if not plan_file.exists():
            return {"status": "error", "message": "Plan not found"}

        content = plan_file.read_text()

        execution_log = f"""

## Execution Log

**Executed at:** {datetime.now().isoformat()}
**Status:** {execution_result.get("status", "unknown")}
**Result:** {execution_result.get("message", "No message")}

"""

        if execution_result.get("status") == "success":
            content = content.replace("status: pending", "status: completed")
            execution_log += "- ✅ Task completed successfully\n"
        else:
            content = content.replace("status: pending", "status: failed")
            execution_log += (
                f"- ❌ Failed: {execution_result.get('error', 'Unknown error')}\n"
            )

        content += execution_log

        plan_file.write_text(content)

        return {
            "status": "success",
            "message": "Plan updated with execution results",
        }

    def suggest_improvements(self, plan_path: str) -> Dict:
        plan_file = Path(plan_path)

        if not plan_file.exists():
            return {"status": "error", "message": "Plan not found"}

        content = plan_file.read_text()

        suggestions = []

        if "⚠️" in content:
            suggestions.append(
                "Consider breaking down risky steps into smaller, safer actions"
            )

        if content.count("- [ ]") > 7:
            suggestions.append(
                "Many steps detected - consider splitting into sub-plans"
            )

        if "approval" not in content.lower():
            suggestions.append(
                "No approval mentioned - verify if human review is needed"
            )

        if "context" in content.lower() and "not provided" in content.lower():
            suggestions.append("More context needed for better planning")

        return {
            "status": "success",
            "plan_path": str(plan_file),
            "suggestions": suggestions,
        }

    def get_reasoning_history(self, limit: int = 20) -> List[Dict]:
        history = []

        if self.plans_dir.exists():
            for plan_file in sorted(
                self.plans_dir.glob("PLAN_*.md"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )[:limit]:
                content = plan_file.read_text()

                import re

                created_match = re.search(r"created:\s*(.+)", content)
                status_match = re.search(r"status:\s*(\w+)", content)

                history.append(
                    {
                        "plan_file": plan_file.name,
                        "created": created_match.group(1)
                        if created_match
                        else "unknown",
                        "status": status_match.group(1) if status_match else "unknown",
                    }
                )

        return history


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Claude Reasoning Engine")
    parser.add_argument("--vault", required=True, help="Path to vault")
    parser.add_argument("--analyze", help="Task data as JSON")
    args = parser.parse_args()

    engine = ClaudeReasoningEngine(args.vault)

    if args.analyze:
        task_data = json.loads(args.analyze)
        result = engine.create_plan(task_data)
        print(json.dumps(result, indent=2))
    else:
        history = engine.get_reasoning_history()
        print(f"Total plans: {len(history)}")


if __name__ == "__main__":
    main()
