1. What I have achieved so far:

I started by pulling cast metadata for 25 movies and 25 TV shows from the public TMDB API. The raw output wasn’t immediately usable, so I cleaned it and reshaped it into a flat table with one row per cast member per title. Each row includes fields like the title, production years, genres, media type, actor name, character name, billing order, and the actor gender as provided by TMDB.

From there, I wrote a parsing script to turn this raw data into something more analytically useful. One of the first fixes was adjusting billing order from zero-indexed to one-indexed, which I then used to assign each cast member to a role tier: lead (positions 1–3), supporting (4–10), or minor (11–20). I also defined a prominence score as the inverse of billing order and normalized it within each title so that all scores sum to 1.0. That way, the values are comparable even when cast sizes differ. In addition, I added a named-character flag to filter out generic or uncredited background roles like “Cop” or “Pedestrian (uncredited),” which ended up making up about 23% of the data.

While setting this up, I made sure the schema could handle later annotation work without needing to be restructured. I included placeholder columns for actor ethnicity, actor sexuality, character-level demographics, mismatch flags, sympathy coding, and arc quality from the beginning. At this point, the dataset contains 696 cast rows across 49 titles, with 535 named characters that are actually used in the analysis.

My next step was figuring out how to actually fill in actor ethnicity and, where possible, sexuality. Doing this manually would have taken too long, so I reused the OpenAI API from a previous MPCS course and wrote a script to categorize actors into a set of fairly coarse groups: “White,” “Black,” “Hispanic/Latino,” “East Asian,” “South Asian,” “Middle Eastern,” “Mixed/Multiracial,” and “Unknown.” I had the model return a confidence level (low, medium, high) for each assignment, along with a short explanation saved to a separate file. I plan to go back and manually verify these annotations by Week 7.

I applied the same approach to actor sexuality, even though publicly available information here is much more limited. The model was guided to use broad categories such as “Straight,” “Gay/Lesbian,” “Bisexual,” “Queer,” and “Unknown.” So far, this hasn’t produced especially informative statistics, since almost all entries were labeled as either straight or unknown, with only a few exceptions. All categorizations and their corresponding explanations are included in the attached CSV files.

As the final part of this week's deliverable I computed some representation metrics from the generated and extracted data. The results are the following:

Representation metrics
Total cast rows:      696
Named characters:     535
Titles:               49
TV shows:             24
Movies:               25
Gender:

Overall:
              count  percent
actor_gender                
male            355     66.4
female          175     32.7
unspecified       5      0.9

By role type:
actor_gender  female  male  unspecified
role_type                              
lead              31    65            1
supporting        70   138            1
minor             74   152            3

As percentages:
actor_gender  female  male  unspecified
role_type                              
lead            32.0  67.0          1.0
supporting      33.5  66.0          0.5
minor           32.3  66.4          1.3

Average prominence score by gender:
actor_gender
female         0.0678
male           0.0721
unspecified    0.0983
Ethnicity:

Overall:
                   count  percent
actor_ethnicity                  
White                378     70.7
Black                 54     10.1
East Asian            38      7.1
Hispanic/Latino       21      3.9
Unknown               19      3.6
Mixed/Multiracial     15      2.8
Middle Eastern         8      1.5
South Asian            2      0.4

By role type:
actor_ethnicity  Black  East Asian  Hispanic/Latino  Middle Eastern  Mixed/Multiracial  South Asian  Unknown  White
role_type                                                                                                          
lead               5.2         5.2              4.1             1.0                3.1          0.0      0.0   81.4
supporting         7.7         6.2              4.3             1.0                2.9          0.5      1.4   76.1
minor             14.4         8.7              3.5             2.2                2.6          0.4      7.0   61.1

Average prominence score by ethnicity:
actor_ethnicity
Mixed/Multiracial    0.1099
White                0.0792
Hispanic/Latino      0.0768
East Asian           0.0466
Black                0.0414
Middle Eastern       0.0383
South Asian          0.0331
Unknown              0.0206

White actors:     378 (70.7%)
Non-white actors: 157 (29.3%)

White vs non-White by role type (% White):
  lead: 81.4% White
  supporting: 76.1% White
  minor: 61.1% White
Sexuality (disclosed only):

Actors with disclosed sexuality: 276 of 535 (51.6%)

Among disclosed actors:
                 count  percent
actor_sexuality                
Straight           273     98.9
Bisexual             3      1.1

Non-straight actors (disclosed): 3

Non-straight actors by role type:
role_type
supporting    2
minor         1

Non-straight actors by gender:
actor_gender
female    3
Intersectionality: Gender × Ethnicity

Lead roles only (97 total):
actor_ethnicity  Black  East Asian  Hispanic/Latino  Middle Eastern  Mixed/Multiracial  White
actor_gender                                                                                 
female               2           2                3               0                  2     22
male                 3           3                1               1                  1     56
unspecified          0           0                0               0                  0      1

Average prominence score by gender × ethnicity:
actor_ethnicity   Black  East Asian  Hispanic/Latino  Middle Eastern  Mixed/Multiracial  South Asian  Unknown   White
actor_gender                                                                                                         
female           0.0476      0.0501           0.0678             NaN             0.0855       0.0199   0.0196  0.0719
male             0.0398      0.0462           0.1056          0.0383             0.1770       0.0463   0.0211  0.0814
unspecified      0.0146      0.0154              NaN             NaN                NaN          NaN   0.0164  0.2226
Trends over time:

'%' Female by decade:
decade
1980s    35.0
1990s    33.3
2000s    30.2
2010s    34.2
2020s    28.8

'%' White by decade:
decade
1980s    90.0
1990s    63.6
2000s    74.1
2010s    68.7
2020s    75.0

Lead role gender split by decade ('%' female leads):
decade
1980s     0.0
1990s    41.7
2000s    44.0
2010s    25.5
2020s    30.0



2. What I am happy with, from my project work so far:

I am happy with the process of pulling, cleaning, and parsing data so far. It works mostly automatic and generates a lot of useful data with an easy way of addingmore later on. The generated prominence score is also a successfull way of comparing data accross different movies and shows, regardless of how big the cast is.
I am also pleased with using the OpenAI API to fill out data that I would have otherwise had to collect manually.
There is also already more insights generated from the representation metrics than I would have initially expected.



3. What I am struggling with, or what challenges I am facing next:
I still have a few open decisions to make around data selection. I know I want to scale the dataset significantly (x10?),but I have not fully settled on what the expanded sample should include.
A few questions that came up for me were:
- Should I use just movies or just tv shows instead of both?
- Should I use only the top rated or top popular titles from TMDB rather than selecting a few from here and a few from there, depending on what I deemed interesting or what I like to watch? (heavy selection bias from my side here)
- If I went with the approach of only pulling the top titles, I fear they would skew heavily toward male-centered narratives (The godfather, wolf of wallstreet, etc...), which would systematically bias the representation metrics before any analysis begins. A top-titles approach risks measuring the genre conventions of blockbuster cinema rather than the industry more broadly.  So far I am unsure on how to decide on this
- A similar question arises with sexuality. Productions that feature a high proportion of queer characters tend to be *explicitly* about queer experiences — meaning any sample that includes them will conflate intentional representation with organic inclusion. Including shows like OITNB show lovely and interesting data, but also inflates the numbers in a way that may obscure rather than reveal how queer characters are woven into mainstream storytelling. The question of whether to include them is essentially a sampling decision: am I measuring how often queer characters appear in media broadly, or how often they appear in media that isn't explicitly about them?
- I am also wondering if I should limit my data to only include US productions?


4. Anything else I’d specifically like the course staff to focus on in giving me feedback or advice:
I would appreciate feedback and opinions to my questions posed in the previous section.