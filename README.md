# Status Waypoint
Helping to navigate the world of airline status, route optimization, and mileage runs. 


## FAQ
### What is this? 
At a high level, this can be used to find high-quality, feasible flight paths that satisfy a set of user-defined constraints. In other words - you tell it what your constraints are, and it'll return the 10 best routes it can find for you. (Note: using beam search so it's not globally optimal but it'll be close).

### Why did we build it? 
I am four flight segments short of re-qualifying for United's Premier Gold status - which I find pretty valuable for both domestic & international travel (see benefits & explanation further down!). With a year-end deadline, I had to figure out what flight path would be a good option for me to close the gap. I didn't want to search manually on Google Flights forever, so I built this to do the work for me. 

### Who is it for? 
Right now, for people like me who have an urgent need to optimize route plans on United Airlines. As it evolves, I see a few other key use-cases: 
- *Stopover Planning* | Looking to do a stopover somewhere for 24 - 48 hours? Use this to plug in the airports you'd want to fly into for your stopover, and see available routes. 
- *Flight Risk Management* | Nervous flyer? Need to fly somewhere where there's no direct route? Use this to find optimal flight paths based on given constraints (like layover time)
- *AvGeeks* | Do you make decisions about what flight to take based on the aircraft type? Me too. With the coming aircraft type constraint, you can filter out routes on those regional jets like CRJ and only fly Dreamliners if you want. 


### Is there a UI for this? 
Not yet. Right now this is all CLI based while it's still in proof of concept mode. Maybe a simple UI for v1, but more than likely that'll be v1.5 or v2. I'm focused on functionality, and then will build the UI. But definitely thinking about UI/UX while building the backend. 

## What are the limitations 
*Network Schedule* | I got the route data from United's website, but it is a static .xlsx file, so any changes to the route plan will not automatically be reflected here. However! In v1, we plan to integrate with an API provider that can give us flight schedules, and we'll eliminate reliance on Excel entirely. 

*Travel time optimization only* | For v0 (aka what you see live now), we don't have price data or additional constraints / filters available yet - we're solely optimizing based on total travel time. This will continue to improve, an v1 will have more filters. Personally - I'm most excited about the aircraft type filter because why wouldn't you want to fly on a B777 for the 90 minute hop from Denver to Las Vegas.

<img src="./assets/images/kaia-united.jpg" width=50% height=50%/>
