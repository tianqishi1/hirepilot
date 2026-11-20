package com.hirepilot.repo;

import com.hirepilot.domain.ChatMessage;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MessageRepo extends JpaRepository<ChatMessage, Long> {
    java.util.List<ChatMessage> findByCandidateIdOrderByIdAsc(Long candidateId);
    java.util.Optional<ChatMessage> findByIdempotencyKey(String idempotencyKey);
}
