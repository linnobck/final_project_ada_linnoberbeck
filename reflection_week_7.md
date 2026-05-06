
1. What you have achieved so far
Since the Week 5 checkpoint, I have achieved the following:
Sexuality was dropped from the analysis as the initial annotation pass made clear there just isn't enough publicly available data to produce anything meaningful, and keeping it would have added more noise than insight. The dataset was also narrowed to US productions only, which makes the findings cleaner and more directly comparable across titles without having to account for cross-cultural differences.
Instead of manually picking titles, I automated the data collection using TMDB's popularity-ranked discovery endpoint, pulling the most-watched US films and TV shows directly. This grew the dataset from 50 hand-picked titles to over 580 productions (roughly 15x bigger) which makes the statistical findings a lot more reliable and removes most of the selection bias from the earlier approach.
I also added two new qualitative dimensions to the annotations: sympathy coding, which captures how the audience is meant to feel about each character (protagonist, antagonist, antihero, redeemed, fallen, or neutral), and arc quality, which looks at whether a character meaningfully changes over the story and in which direction. Both were generated using the OpenAI API, with a confidence flag on each entry so I know which ones need manual review.
The analysis itself has gotten considerably deeper too. On top of basic counts and proportions, I'm now looking at trends over time, lead versus supporting role breakdowns, intersectional comparisons of gender and ethnicity together, and differences across media type and genre. All statistical tests are corrected for multiple comparisons using the Benjamini-Hochberg procedure, and everything is visualized in a Colab notebook with annotated charts for each section.


2. What you are happy with, from your project work so far
I am happy with how the data pipeline worked out for me, as it made it pretty easy for me to increase the size of my data set, eventhough it took some time to fully run, especially the annotations.
The created dataset has a lot of potential insights available, which have been vizualised in the notebook!


3. What you are struggling with, or what challenges you are facing next 
The next challenge is finding a way to meaningfully incorporate the sympathy coding and arc development data into the analysis. Right now they exist as annotations but haven't been connected to the representation metrics yet. Verifying over 7,000 AI-generated classifications is also difficult at this scale, so some sampling strategy for manual review will be needed. After having to drop sexuality from the analysis, I'm hoping these dimensions will add the kind of qualitative depth the project needs.
The statistical analysis also still has room to grow. I want to think more carefully about what additional comparisons make sense given the data I have, particularly once the arc and sympathy columns are integrated.
Actor-character demographic mismatches, where an actor's gender or ethnicity differs from the character they're playing, are still potentially on the table. This is one of the more interesting structural questions the dataset can answer, and I'd like to include it if the annotation effort is manageable.
For the final checkpoint, the goal is to have all data finalized and cleaned, and to build an interactive interface that lets users customize what gets displayed and how, filtering by genre, decade, media type, or demographic group. I'd also like to include some notes on how the pipeline could be extended to other datasets beyond US productions.


4. Anything else you’d specifically like the course staff to focus on in giving you feedback or advice
In your last feedback you mentioned to include some visuals, so I hope the included ones are a good start.
I also talked to Chelsea about the AI generated data and we agreed that as long as I manually check it, that procedure is fine.
A better discription of prominence score was included in the notebook, please let me know if it is making sense now.
