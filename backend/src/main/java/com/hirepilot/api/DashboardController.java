package com.hirepilot.api;

import com.hirepilot.service.WorkflowService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {
    private final WorkflowService workflow;
    public DashboardController(WorkflowService w) { workflow = w; }

    @GetMapping
    public Map<String, Object> dashboard(@RequestParam Long jobId) { return workflow.dashboard(jobId); }
}