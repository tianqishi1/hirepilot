package com.hirepilot.repo;

import com.hirepilot.domain.RunRequest;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface RunRequestRepo extends JpaRepository<RunRequest, Long> {
    Optional<RunRequest> findFirstByStateOrderByIdAsc(String state);
    List<RunRequest> findByJobIdOrderByIdDesc(Long jobId);
    boolean existsByJobIdAndStateIn(Long jobId, List<String> states);
}