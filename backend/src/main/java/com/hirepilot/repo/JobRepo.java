package com.hirepilot.repo;

import com.hirepilot.domain.Job;
import org.springframework.data.jpa.repository.JpaRepository;

public interface JobRepo extends JpaRepository<Job, Long> {
}
