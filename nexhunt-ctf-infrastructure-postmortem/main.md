# NexHunt CTF 2025 Infrastructure Postmortem

**Authors:** 0xkatana  
**Date:** December 15, 2025  
**Reading time:** 10 min  
**Tags:** postmortem, infrastructure

## Introduction

This year marked the our first global ctf [NexHunt CTF](https://ctftime.org/event/3037), the ctf was public to  participants from around the world with ctfd. As first-time organizers, we aimed to make  a high-quality CTF experience with challenging problems and stable infrastructure and aim for a good ctfd weight. However,the ctf event was stable for a first-time and we hade a huge ammount of players thank you guys we had almost 2k players and 1k team , we encountered some  infrastructure  challenges during the event. This postmortem documents our experiences, challenges, and lessons learned to improve future iterations.

i was the main (0xkatana) the main one managing the infrastructure and challenges repository. Special thanks to L4ZEX for helping with challenge setup and NIL for monitoring challenges throughout the event.

## Event Statistics

- **Participants:** 1,909 users registered
- **Teams:** 997 teams registered
- **Unique IP addresses:** 36,095
- **Total possible points:** 15,153
- **Challenges:** 62
- **Most solved challenge:** HuntMe1 with 410 solves
- **Least solved challenge:** Labyrinth with 1 solve
- **Event duration:** 3 days
- **Start time:** December 11, 2025, 18:00 UTC
- **Overall uptime:** 99.85%

### Category Breakdown
- **Beginner:** 6 challenges
- **Blockchain:** 4 challenges
- **Crypto:** 5 challenges
- **Feedback:** 1 challenge
- **Forensics:** 7 challenges
- **Malware:** 1 challenge
- **Misc:** 7 challenges
- **OSINT:** 7 challenges
- **Pwn:** 6 challenges
- **Reverse:** 9 challenges
- **Web:** 9 challenges

### Submission Statistics
- **Fails:** 21,135
- **Solves:** 4,368

### Point Distribution
- **Beginner:** 908 points
- **Blockchain:** 569 points
- **Crypto:** 1,684 points
- **Feedback:** 1 point
- **Forensics:** 2,366 points
- **Malware:** 500 points
- **Misc:** 1,132 points
- **OSINT:** 2,403 points
- **Pwn:** 1,816 points
- **Reverse:** 1,700 points
- **Web:** 2,074 points

## Infrastructure Overview

Our infrastructure consisted of two main servers:
1. **Platform server:** Running CTFd platform  behind a cloudflare proxy , cdn and firewall and we used  Google Gmail for email services
by our hosting partner [Hawiyat.org](https://hawiyat.org)

2. **Challenge server:** A powerful Threadripper server (24 cores, 128GB RAM) provided by our hosting partner [Hawiyat.org](https://hawiyat.org)

We implemented Cloudflare as our WAF, CDN, and reverse proxy to protect the platform. The challenge deployment infrastructure was set up just 2 days prior to the event due to time constraints, which led to several issues that are detailed below.

### Monitoring Setup

We used multiple combinations to monitor our servers and infrastructure. Our monitoring stack included:
- **Portainer** for container management
- **Uptime Kuma** for uptime monitoring
- **Bezel** for notifications
- **Monitour** for tracking any downtime

All monitoring tools were linked with our Discord server to notify us directly of any issues, ensuring rapid response to infrastructure problems.

## Performance Statistics

During the CTF, we served a total of 2 million requests through CTFd. Cloudflare cached 25% of these requests, which contributed to improved uptime and performance. Our final uptime accuracy reached 99.92% over the last 3 days of the event, with 100% uptime during the final day. The average response time was 190ms, demonstrating the effectiveness of our caching and infrastructure setup despite the high load.

![Cloudflare Requests](./cloudflare-requests.png)
*Cloudflare dashboard showing request volumes during the CTF*

![Uptime Monitoring](./uptime.png)
*Uptime monitoring dashboard showing service availability*

![Server 1 Usage A](./srv-1-usage-a.png)
*Platform server usage metrics at time A*

![Server 1 Usage B](./srv-1-usage-b.png)
*Platform server usage metrics at time B*

![Server 2 Usage A](./srv-2-usage-a.png)
*Challenge server usage metrics at time A*

![Server 2 Usage B](./srv-2-usage-b.png)
*Challenge server usage metrics at time B*

![Response Time and Monitoring](./response-time-uptime-monitoring.png)
*Response time and uptime monitoring during the event*

## Challenges Faced During the Event

### Platform Load Issues

As soon as the CTF started, we experienced a surge in traffic with over 30,000 requests in the first minute. This caused our platform latency to spike to 4.5 seconds. However, the system stabilized after approximately 3 minutes, returning to sub-200ms response times.
this was to the lack of the cache hits from the cdn and no ratelimiting rules
### Email Limitations

We quickly hit Google Gmail's daily email limits after sending over 1,000 emails. This made email delivery slow and unreliable, particularly for verification emails. We had to disable email verification within the first hour of the competition to prevent further issues.

### DDoS Attacks

We experienced 2 downtime periods caused by DDoS attacks that bypassed Cloudflare's anti-DDoS and bot protection. Although Cloudflare's protection caught most attacks, some smart endpoints were exploited. Despite these attacks, we maintained an overall uptime of 99.85% over the 3-day event.

### Cloudflare Caching Issues

During one incident, we accidentally enabled an aggressive cache-all rule in Cloudflare, which negatively impacted user experience. Players received cached pages and cookies from other users, causing scoreboard mix-ups and challenges appearing as solved when they weren't. We issued an announcement asking participants to clear their browser cache to resolve the issue.

Timeline:
- Platform latency spike: 4.5 seconds in first minute, stabilized after 2 minutes to sub-200ms
- DDoS attack: 2-minute attack causing 7-second latency
- Cloudflare caching issue: Brief but impactful to user experience

### Docker Swarm Load Balancer Issues

Our challenges were deployed using a combination of Docker Swarm services and stacks with load balancers between instances. We averaged 10 instances per challenge, with web challenges having more than 10+ instances. However, we encountered issues with Docker Swarm's port load balancer failing to forward traffic. The resolution required scaling down services to zero and then rescaling them.

### Challenge-Specific Issues

Multiple web challenges experienced failures, most notably "secure storage," which required multiple scaling attempts before being taken down for the next wave of fixes.

Some challenges, particularly "Labyrinth," caused very high resource usage since containers weren't properly limited. This caused our challenge server's CPU usage to reach 70%. Implementing resource limits on containers and scaling to more instances resolved the issue.

### Resource Management

Since we didn't have time to set up proper instancer plugins (most challenges didn't require instances), we used Docker Swarm services and stacks with load balancers. We used automation to bring up challenges and scale them, with Portainer helping us manage them more efficiently.

## Timeline of Major Incidents

- **Dec 11, 18:00 UTC** - CTF started with over 30k requests in first minute
- **Dec 11, 18:01 UTC** - Platform latency spikes to 4.5 seconds
- **Dec 11, 18:03 UTC** - Platform stabilizes to sub-200ms response times
- **Dec 11, 19:00 UTC** - Email verification disabled due to Gmail limits
- **Dec 11, 20:00 UTC** - Secure storage challenge fails multiple times
- **Dec 11, 23:05 UTC** - Docker swarm load balancer fails, services scaled to zero and back
- **Dec 12, 4:00 UTC** - First DDoS attack bypassing Cloudflare protections
- **Dec 12, 4:10 UTC** - Accidental aggressive caching rule causes user session issues
- **Dec 12, 4:11 UTC** - Issue fixed, but propagation causes continued problems
- **Dec 12, 4:15 UTC** - Announcement issued for users to clear browser cache
- **Dec 12-13** - Second phase of CTF mostly stable with minimal noticeable problems some downtime for web/pwn challengs but not a big deal
- **Dec 12** - Labyrinth challenge resource usage causes 70% CPU on challenge server

## Conclusion

Running custom infrastructure for a CTF is definitely not for the faint of heart. We took the risk by building our own solution with limited time, and though we encountered several issues during the event, we were able to maintain 99.85% uptime over the 3-day competition. While there were many challenges, we consider this a success for our first-time event.

Although we had to implement many systems during the final 2 days before the CTF, we managed to keep the platform running with only minimal downtime. The experience taught us valuable lessons about infrastructure planning, resource management, and the importance of stress testing before the event.

Organizing our first NexHunt CTF was a learning experience that will undoubtedly improve our future events. The feedback and experience gained will help us deliver an even better experience next year.
