
.;,;.
Posts
Contests
Members
About
Introduction, GCP

Introduction, GCP
Introduction, GCP

Blog

    smileyCTF 2025 Infrastructure Postmortem

smileyCTF 2025 Infrastructure Postmortem
smileyCTF 2025 Infrastructure Postmortem
ani
ani
,
voxxal
voxxal
,
jayden
jayden
June 18, 2025
15 min read
postmortem
Previous Post TJCTF 2025 Writeups
Next Post UIUCTF 2025: "Bootkit"
Introduction

This year while planning for the inaugural smileyCTF, we decided that existing infrastructure solutions were not suitable for our needs. We decided to start from scratch and write brand new software for our competition. We were pressed for time, and this led to a lot of issues arising during the CTF, causing our infrastructure to frequently be unresponsive or go down. We’re sincerely sorry for all the issues our infrastructure has caused. Thankfully, most of the issues have been ironed out, and next year will be much better.

We had the bright idea to postpone work on this infra until 2 weeks prior to the CTF, with the deployer only getting real testing the day before. Worse, many of the issues we ran into likely would not have been caught without a full stress test :(

Timestamps should display in your local timezone, without JS they will fallback to PST, year 2025
GCP

As soon as the CTF started, people instantly began reporting that the site was down. What? It turns out that our GCP platform VM (2 vCPUs/2GB) was unable to handle the load. Worse, our quota was quite low: only 12 vCPUs. First, we scaled the platform VM to 8 vCPUs and 8GB, but that only left 4 vCPUs and 4GB for the challenge VM! And so we downscaled the platform VM to 4 vCPUs and 4GB so we could give the challenges VM 8 vCPUs and 32GB. However, ultimately, that did not end up being enough. We then shuffled some more resources to the platform VM, leaving the challenges VM completely starved again. This led to us moving the challenge VM off GCP and onto AWS, where we gave it 32 vCPUs and 32GB, which seemed to be enough.

Timeline:

    2025-06-14 01:00 - CTF started
        Platform VM was e2-standard-2; 2 vCPUs, 8 GB RAM
        Challenge VM was n2-highcpu-4; 4 vCPUs, 4 GB RAM
    2025-06-14 01:01 - Reports of platform being down
    2025-06-14 01:05 - Platform VM taken down on GCP to scale up resources
    2025-06-14 01:09 - Platform VM scaled up to e2-standard-8; 8 vCPU, 32 GB RAM
    2025-06-14 01:10 - Platform VM started
    2025-06-14 01:18 - Platform is back up
    2025-06-14 01:23 - Challenge VM taken down on GCP to scale up resources
    2025-06-14 01:27 - Attempted to scale challenge VM
        Challenge VM scaled up to n2-highcpu-64; 64 vCPUs, 64 GB RAM
    2025-06-14 01:28 - Attempted to start challenge VM
        Failed to start due to quota restrictions
    2025-06-14 01:31 - Platform VM is taken down to scale down resources
    2025-06-14 01:33 - VMs rescaled
        Platform VM scaled down to e2-standard-4; 4 vCPUs, 16 GB RAM
        Challenge VM scaled up to n2-highmem-8; 8 vCPUs, 64 GB RAM
    2025-06-14 01:35 - VMs started
    2025-06-14 01:36 - Platform is back up
    2025-06-14 02:03 - Non-instanced remote challenges are back up
    2025-06-14 02:10 - Challenge VM created on AWS, migration began
        New challenge VM was c5a.8xlarge; 32 vCPUs, 64 GB RAM
    2025-06-14 02:36 - Non-instanced remote challenges are back up on the AWS VM
    2025-06-14 03:27 - Challenge VM deleted on GCP

Email

Email was something I (jayden) added for fun, but we quickly realized its utility when people needed a way to recover their team tokens and Discord tickets started coming in requesting us to recover them. I decided to use Azure’s Email Communication Service, which proved to be a mistake.

After ~1,800 emails were sent on the first day of the CTF, we hit some sort of limit. We quickly removed it from the platform and handled token recovery manually via Discord tickets in the interim. Azure’s API response claimed it was a PerSubscriptionPerHourLimitExceeded error, so naturally I tried waiting an hour. After waiting and trying to send an email again, it still didn’t work (thanks Azure!)

Also, quota increases for email on Azure apparently took up to 72 hours to process. That means it could potentially only process well after the CTF ended. Obviously, not going to work.

So, I tried pivoting to AWS’s Simple Email Service.
Email from Amazon Web Services <no-reply-aws@amazon.com>

Hello,


Thank you for submitting your request to increase your sending limits. We w=

ould like to gather more information about your use case.


If you can provide additional information about how you plan to use Amazon =

SES, we will review the information to understand how you are sending [...]

In your response, include as much detail as you can about your email-sending=

processes and procedures


[...]


You can provide this information by replying to this message. Our team prov=

ides an initial response to your request within 24 hours. [...]

“within 24 hours”? Well, that’s not going to work. How about SendGrid?
Email from Twilio Support <support@twiliosendgrid.zendesk.com>

Hello,


We appreciate your interest in Twilio SendGrid and your efforts in completing=

our account creation process. After a thorough review, we regret to inform yo=

u that we are unable to proceed with activating your account.

Okay, I didn’t realize it was so hard to give your money to email providers in 2025.

Finally, I turned to Proton Mail’s SMTP. We already use Proton as our team’s main email provider, so signing up for a new service that would probably just “fraud-gate” me again wasn’t necessary.

I was hesitant to use it, which is why I tried other services first. I’ve used their SMTP before, for vsCTF, and had problems with emails becoming increasingly delayed after a certain volume. Presumably, it’s made for low volume use-cases; not for handling a thousand emails a day. However, at this point it had been almost 2 hours and we needed something working fast.

This time around there were no email delay issues and it worked perfectly, sending another ~1,400 emails until the end of the CTF!

Screenshot_20250618_111334

Lesson learned. Thanks to the state of email fraud, providers never trust you, even if you have your wallet out. Always establish your email provider account well before you do anything with it. Otherwise, you will be in for a very annoying time.

Timeline:

    2025-06-14 01:43 - Email quota is reached, people are unable to register or recover their token
    2025-06-14 01:48 - Email verification is disabled on the platform
    2025-06-14 04:14 - Email verification is re-enabled on the platform (switched to Proton Mail SMTP)

Ratelimiting

After we realized that our challenge deployment endpoint was getting hammered, we decided to employ ratelimits to prevent people from destroying our servers. By default, tower_governor uses the PeerIpKeyExtractor which is not what we wanted, but since I (voxal) was in a rush, I neglected to read the docs:

    A KeyExtractor that uses peer IP as key. This is the default key extractor and it may not do what you want.

    Warning: this key extractor enforces rate limiting based on the peer IP address.

    This means that if your app is deployed behind a reverse proxy, the peer IP address will always be the proxy’s IP address. In this case, rate limiting will be applied to all incoming requests as if they were from the same user.

This brought down all the challenge endpoints (listing, deploying, submitting, etc.) for about 5 minutes before it was disabled, and later switched to the SmartIpKeyExtractor.

Timeline:

    2025-06-14 02:09 - Faulty ratelimiting code was deployed
    2025-06-14 02:14 - Disabled ratelimiting code
    2025-06-14 03:01 - Ratelimiting code fixed and deployed

Multi-container support

One thing that we wanted to support in the deployer (that ended up being cut due to time constraints) was multi-container provisioning for instanced challenges. However, as it turned out, two of our challenges (misc/multisig-wallet and misc/vs-math-ai) actually required two containers. Quasar (goat) was somehow able to port multisig-wallet to only use one container by the time that I (ani) had finished drafting and locally testing multi-container support. Initially, due to the lack of multi-container provisioning, vs-math-ai was manually deployed as a shared remote challenge. However, since the challenge required getting RCE in one of the containers, any crashes in that container ended up impacting everyone, which was not good! After multi-container support was merged into the deployer (and some brief downtime), we switched vs-math-ai to be an instanced challenge, so that everyone would get their own instance, avoiding the above issue with crashes!

Timeline:

    2025-06-14 06:41 - Work on making multisig-wallet a single container begins
    2025-06-14 08:33 - Work on multi-container support begins
    2025-06-14 09:00 - Work on making multisig-wallet a single container is finished
    2025-06-14 10:26 - Multi-container support is merged and challenges are updated
    2025-06-14 10:35 - It is found that Docker does not have enough subnet space by default to accommodate the number of networks being created
    2025-06-14 10:45 - Remotes are back up after subnet space was adjusted (thanks Reddit)
    2025-06-15 01:02 - vs-math-ai is switched to instanced

Other miscellaneous instancing issues

In no specific chronological order, here are some other minor issues/bugs that we ran into and fixed:

    People spamming the instancing buttons leading to weird, but not incorrect, behavior
    People not knowing their teammates modified instances
    Not expiring instances properly on frontend
    Unclean deployer shutdown
    Lack of deployer resiliency
        This actually ended up being important so that users could “unstuck” the system from bad states
    Adding a destroy button for users
        This feature was also important for “unstucking”
    Lack of cooldown on destroy instance button in frontend
    Container reaping

Unkeyed challenges

We received a lot of reports of challenges having instances where they shouldn’t be having them. This turned out to be because I (voxal) forgot to key the list, leading them to be keyed by index. That meant if you turned on a filter, the instance data would stay connected to the index, making challenges without instances seem like they did, causing a lot of confusion.
Caddy admin API

This was a bug that was quite pervasive during the entire CTF in which connections would randomly get dropped. We decided to use the Caddy admin API to dynamically update reverse proxy endpoints as instances were created and destroyed. However, what we did not foresee is that the admin API restarts the entire server whenever you modify the configuration. To work around this bug, we created a Caddy module that looks up subdomains using an in-memory hashmap, which didn’t require a config change. This put the final nail in the coffin for the spotty instance URLs.

Timeline:

    2025-06-14 19:50 - It is suspected that there is a bigger issue with Caddy’s web serving
    2025-06-14 20:06 - voxal suspects the issue is with Caddy’s admin API
    2025-06-14 20:16 - Debug logs are added to Caddy
    2025-06-14 20:21 - QUIC (HTTP/3) is disabled (this does not help)
    2025-06-14 20:43 - Confirmed that the issue is with Caddy’s admin API
    2025-06-14 21:48 - Work begins on the new caddyrouter plugin
    2025-06-15 00:45 - New caddyrouter plugin is deployed and used

Firefox and resource limits

There was one series of web challenges that were different from the other challenges: web/teemos-secret and web/teemos-secret-v2 by Chara. Unlike others, these used Firefox admin bots over the standard Chrome as they relied on Firefox-specific behavior.

The first teemos-secret was deployed at around 19:20 PST. For several hours, everything ran fine, until around 05:18 PST the next day where I (jayden) noticed the challenge VM died. I was the only infra admin online at the time, so it was up to me to fix this.

The reason the challenge VM “died” was due to a player’s exploit causing Firefox RAM usage to balloon out of control. Once Firefox ate up all the RAM on the system, it became unresponsive. The OOM killer is supposed to kill the process eating up the most RAM on the system, however due to certain factors such as memory pressure severity, or thrashing (when the system spends a lot of time swapping to disk), it can take a very long time.

Two main factors significantly increased the time it took to resolve this issue:

First, I was unfamiliar with the deployer setup (written by ani and voxal), meaning I had to quickly familiarize myself with the deployer and setup while responding to the incident. Also, I had to do most of it from my phone 🤯

Second, while we frantically moved from GCP to AWS (see GCP ), I forgot to give the new challenge VM an “elastic” (static) IP. The deployer authenticates with the Docker API using a peer certificate that has the challenge VM’s IP as the Subject Alternative Name (SAN). Due to this, every time the VM’s IP changed, it failed to authenticate, causing me to have to reissue the cert and update it in the configs. After the first force-stop and start, I gave it a static IP, so subsequent redeploys were faster.

Timeline

    2025-06-15 03:20 - web/teemos-secret deployed
    2025-06-15 08:00 - web/teemos-secret-v2 deployed
    2025-06-15 13:18 - Player runs memory-intensive exploit, Firefox memory usage quickly balloons
    2025-06-15 13:20 - Challenge VM runs out of memory, unresponsive due to OOM condition
    2025-06-15 13:24 - Challenge VM force-stop initiated
    2025-06-15 13:32 - Challenge VM force-stop complete and start initiated
    2025-06-15 13:34 - Challenge VM started
        VM IP changes as it did not have an assigned static IP
    2025-06-15 13:35 - smiley.cat A records changed
    2025-06-15 13:36 - Attempted to restart deployer on Platform VM
        Failed as the IP changed and Docker peer certificate is issued to old IP
    2025-06-15 13:38 - jayden starts to read the deployer code and reverse engineer the setup
    2025-06-15 14:39 - Peer certificate properly reissued. Deployer online; instanced challenges work properly
    2025-06-15 14:46 - Challenges with static remotes back online
    2025-06-15 15:06 - Player runs memory-intensive exploit
    2025-06-15 15:07 - Challenge VM out of memory and unresponsive again
    2025-06-15 15:09 - Challenge VM force-stop initiated
    2025-06-15 15:12 - Static IP issued and attached to VM
    2025-06-15 15:14 - smiley.cat A records changed
    2025-06-15 15:17 - Challenge VM force-stop complete and start initiated
    2025-06-15 15:20 - Challenge VM started
    2025-06-15 15:35 - Peer certificates reissued, deployer restarted and online, static remotes redeployed and back online
    2025-06-15 16:01 - Author applies patches to the admin bot in an attempt to mitigate the issue
    2025-06-15 16:40 - Player runs memory-intensive exploit
    2025-06-15 16:41 - Instance force-stop initiated
    2025-06-15 16:50 - Instance force-stop complete and started
    2025-06-15 16:54 - Everything is quickly brought back up again
    2025-06-15 16:56 - Creating new web/teemos-secret instances is disabled; source is left up to allow local solves
        web/teemos-secret-2 taken offline permanently at author’s request
    2025-06-15 20:24 - Implementation work starts on resource limit configuration
    2025-06-15 20:42 - Resource limits implemented
    2025-06-15 21:18 - web/teemos-secret redeployed with limits

Conclusion

Implementing custom infrastructure is definitely not for the faint of heart. We gambled when we decided to do it, and luckily it didn’t turn out to be completely useless. Although there were many issues, there could have been many more and we are glad it was worth our time and effort. Writing our own infrastructure afforded us a lot of flexibility, which turned out to be somewhat useful in the CTF, compared to just running something like rCTF.

Anyways, we hope you enjoyed this infrastructure postmortem!
Bonus Q&A

Shortly after this post was published, we had a participant from our Discord ask us a few questions. The questions and answers are reproduced below.

Questions:

    from the blog post:

        Writing our own infrastructure afforded us a lot of flexibility, which turned out to be somewhat useful in the CTF, compared to just running something like rCTF

        What were the advantages and disadvantages of running custom infra? How experienced you were with hosting stuff in the cloud?

        What are your main tips for a team that has experience playing ctfs, but is hosting one for the first time?

        How long did it take to do it? (Ex: When the planning started, what took the most time etc)

Answers:

    The main reason to run custom infra is that most of the existing options suck. Many of the other options require other random services (like redis or k8s) and were not as easy to work with. Writing custom infra allowed us to improve on existing options, and gave us a lot more control with how well integrated all the different features were, and as a bonus adding new features is drastically easier (plus it was a lot of fun). For example rCTF does not have any instancing integration, yet with our custom infra we were able to give it first-party support.

    One of our team members has experience trying to add new features to rCTF, and they say “since adding new features required hooking it into 10 different places, any time you wanted to do anything, since every change ended up touching so many systems, it was a pain to get anything done”

    Our main suggestion is to not write your own infra. Use an off-the-shelf solution and focus more on challenge quality and stability. Make sure all challenges are done prior to the CTF and make sure your solve scripts for each challenge work properly on remote. For smileyCTF, most of us already had experience running prior CTFs (vsCTF, amateursCTF) for years, so we felt like we got our feet wet enough to write our own infra.

    Infra took around 2 weeks but we also had deep knowledge of how CTF platforms worked already (having experience writing instancers and other infra before). If you are unfamiliar, it may take a few extra weeks. For the CTF itself, most of the time was spent writing challenges so this depends how many people/challenges you have.

Previous Post TJCTF 2025 Writeups
Next Post UIUCTF 2025: "Bootkit"

© 2025 smiley foundation, 501(c)(3)

