


This year is the first version https://ctftime.org/event/3037 , and we got a wieght total  23.73  i was mainly the one manging the infrastrucre and challenges repo since im the tech manger , L4ZEX was a greate help in setinup challenges and also NIL for monitoring challengse 

we had a total 
1909 users registered
997 teams registered
36095 IP addresses
15153 total possible points
62 challenges
HuntMe1 has the most solves with
410 solves
Labyrinth  , has the least solves with
1 solves


started at 11 Dec. 2025, 18:00 UTC  
the infrastructe of the event was started 2 weeks before the evnet we had 2 serves first one for ctfd instance and one for the challenges the server for ctfd was setup 2 weeks before the event , with google gmail to send the email the server was from our provider hawiyat.org ( check them out ) , we used cloudflare as our waf / cdn and revesr proxy to protcet the platform , we didn't for the ctfd we didnht had many down times first minute of the ctf more thant 30k requests was served that caused the latecny to reach 4.5 seconds but it stable after 3 minutes back to sub 200ms
we had 2 downtimes caused of a DDos attack that was able to bypass cloudflare antiddos and bot protection through some smart endpontins we had a total uptime of % 99.85 in the 3 days for ctfd , the other issue we faced is reaching googlegmail daily mail limits so we stoped the email verification in the hour that the ctf started 

for the chalelne server Hawiyat gave us a beffy thread ripper server 128 RAM , 24 cores 


for challenges deployment infra was mainlay in our beffy server srv-2-hawiyat (we didnt have time to do it so it was all done 2 days be fore the events )

since we didnt have time to setup instancer plugins and most of the cahllengs didnt need instances we used a combination of docker swarm services and stacks with loadbalancer between instances we avearged 10 instnaces for each challenge and sub web challengs had more than 10+ instances , we used aoutomation to bring challenges an scaled them up , then we used portinaer to mangm them faster and bring them up or scaled them faster 




issues timeline :

    mails failling after more thant 1000+email and almsot 500 in that day it made emails too solw ot reach so we stoped it 


    platform latency +4.5seconds in first min than stableized after 2 minues to sub 200ms 


    multiple web challengs failling mainly secure storage we had to scale it multipe times then we had to tkae it down to  hte next wave for fixes 

    issues with dockerswarm port loadblancer failling to forward anymore to fix it we had to scale down to zero then rescalel them 


    we got a ddos to the platfrom that was the ddos was for a 2 minute and latency reached 7seconds we did more protection and acicdenlty used a cache all rule in cloudflare (lol anyone nows that is bad ) it was fixed almost instnacly under 1 min but the issue has already propagated 

    cloudfalre chaching pages and coockies of other playeres caused a big issue players having new scoreboards of others , challengs apearing solved but not really solved we dead an annoucment to tell the guys to clear the browser cache 

    apart form this main down time in the second phase of the ctf was pretty stable without any noticibale prbolesms 


    some challengs caused a very hight usage since thye aren;t limited it caused the cpu of our challengs server to reach 70% the challenges is mainly labryinth since it needed automation limitint resouce usage of the container and scaling to mroe instnace resovled the issue 




conclustions : 

    using a better email or own email provider 

    use of a caddy/nginx nextime for challenges loadblancing instead of swarm for stablilty and clean acess

    use instaning integrations nexttime 

    use of k3s instead of docker searm (lol if i had time )