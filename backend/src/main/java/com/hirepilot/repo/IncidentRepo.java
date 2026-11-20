package com.hirepilot.repo;

import com.hirepilot.domain.Incident;
import org.springframework.data.jpa.repository.JpaRepository;

public interface IncidentRepo extends JpaRepository<Incident, Long> {
}
