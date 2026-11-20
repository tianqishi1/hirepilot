package com.hirepilot.repo;

import com.hirepilot.domain.ReviewItem;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ReviewRepo extends JpaRepository<ReviewItem, Long> {
    java.util.List<ReviewItem> findByDecision(String decision);
    java.util.Optional<ReviewItem> findFirstByCandidateIdAndDecisionOrderByIdDesc(Long candidateId, String decision);
    void deleteByCandidateIdIn(java.util.List<Long> candidateIds);
}
