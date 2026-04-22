from kube_research_aiq.llm import LlmClient
from kube_research_aiq.models import JobStatus, ResearchDepth, ResearchJob
from kube_research_aiq.settings import Settings
from kube_research_aiq.store import JobStore


class ResearchRunner:
    def __init__(self, settings: Settings, store: JobStore):
        self.settings = settings
        self.store = store
        self.llm = LlmClient(settings)

    async def run(self, job_id: str) -> ResearchJob:
        job = self.store.get(job_id)
        if not job:
            raise ValueError(f"job {job_id} does not exist")

        job.status = JobStatus.running
        job.error = None
        job.selected_depth = self._select_depth(job)
        self.store.save(job)

        try:
            if job.selected_depth == ResearchDepth.deep:
                job = await self._run_deep(job)
            else:
                job = await self._run_shallow(job)
            job.status = JobStatus.succeeded
        except Exception as exc:  # noqa: BLE001
            job.status = JobStatus.failed
            job.error = str(exc)
        self.store.save(job)
        return job

    def _select_depth(self, job: ResearchJob) -> ResearchDepth:
        if job.request.depth != ResearchDepth.auto:
            return job.request.depth
        query = job.request.query.lower()
        deep_markers = ["compare", "evaluate", "architecture", "strategy", "tradeoff", "research"]
        return ResearchDepth.deep if any(marker in query for marker in deep_markers) else ResearchDepth.shallow

    async def _run_shallow(self, job: ResearchJob) -> ResearchJob:
        job.plan = [
            "Classify the request and scope the answer.",
            "Draft a concise response with assumptions and citations.",
        ]
        self.store.save(job)
        answer = await self.llm.complete(
            model=self.settings.shallow_model,
            system="You are the shallow AI-Q researcher. Give concise, cited answers.",
            user=job.request.query,
        )
        job.report = f"# Shallow Research Report\n\n{answer}\n"
        job.citations = ["NVIDIA AI-Q Blueprint", "Project runtime configuration"]
        job.metadata["mode"] = "shallow"
        return job

    async def _run_deep(self, job: ResearchJob) -> ResearchJob:
        job.plan = [
            "Create a research plan and identify decision criteria.",
            "Explore implementation options and operational risks.",
            "Synthesize a portfolio-ready recommendation.",
        ]
        self.store.save(job)

        planning = await self.llm.complete(
            model=self.settings.deep_model,
            system="You are the deep AI-Q planner. Produce a structured investigation plan.",
            user=job.request.query,
        )
        synthesis = await self.llm.complete(
            model=self.settings.deep_model,
            system="You are the deep AI-Q synthesizer. Produce an evidence-backed report.",
            user=f"Original query:\n{job.request.query}\n\nPlan:\n{planning}",
        )
        job.report = (
            "# Deep Research Report\n\n"
            "## Plan\n\n"
            f"{planning}\n\n"
            "## Synthesis\n\n"
            f"{synthesis}\n"
        )
        job.citations = [
            "NVIDIA AI-Q Blueprint",
            "NVIDIA NeMo Agent Toolkit patterns",
            "KubeResearch AIQ workflow config",
        ]
        job.metadata["mode"] = "deep"
        return job
