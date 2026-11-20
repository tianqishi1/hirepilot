package com.hirepilot.repo;

import com.hirepilot.domain.Candidate;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CandidateRepo extends JpaRepository<Candidate, Long> {
    java.util.List<Candidate> findByJobId(Long jobId);
    java.util.List<Candidate> findByJobIdAndStatus(Long jobId, String status);
    java.util.Optional<Candidate> findByJobIdAndExternalId(Long jobId, String externalId);
    long countByJobIdAndStatus(Long jobId, String status);
    void deleteByJobId(Long jobId);
}
