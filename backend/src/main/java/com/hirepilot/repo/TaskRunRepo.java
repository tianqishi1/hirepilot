package com.hirepilot.repo;

import com.hirepilot.domain.TaskRun;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TaskRunRepo extends JpaRepository<TaskRun, Long> {
    java.util.List<TaskRun> findByJobIdAndState(Long jobId, String state);
    void deleteByJobId(Long jobId);
}
