package com.hirepilot;

import com.hirepilot.domain.Job;
import com.hirepilot.repo.JobRepo;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class HirepilotApplication {
    public static void main(String[] args) { SpringApplication.run(HirepilotApplication.class, args); }

    @Bean
    ApplicationRunner seed(JobRepo jobs) {
        return args -> {
            if (jobs.count() > 0) return;
            Job j = new Job();
            j.title = "资深Java工程师（远程）";
            j.jdText = "负责业务全流程自动化：Java/Spring Boot 业务服务开发，浏览器自动化与RPA，大模型在简历评估、信息理解、自动回复场景的应用。要求3年以上Java经验，熟悉Spring Boot、PostgreSQL，熟悉JavaScript/Python者优先。";
            j.hardFilters = """
                {"minYears": 3, "degree": "本科", "mustSkills": ["Java", "Spring"]}
                """;
            j.rubric = """
                {"weights": {"skill": 40, "experience": 30, "education": 20, "stability": 10}, "rejectLine": 60}
                """;
            j.faq = """
                {"薪资范围": "20-30K，14薪，具体面议", "工作地点": "杭州滨江区，支持全职远程办公", "远程政策": "全职远程，每季度一次线下团建", "工时制度": "弹性工作制，双休", "技术栈": "Java/Spring Boot + PostgreSQL，自动化侧 Python/Playwright", "团队": "团队约10人，该岗位直接汇报给研发负责人", "出差": "无需出差，支持全职远程"}
                """;
            j.greetingStyle = "专业、简洁、突出候选人亮点，不超过120字";
            j.dailyLimit = 20;
            jobs.save(j);
        };
    }
}