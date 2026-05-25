To view dashboard open: https://finalprojectadalinnoberbeck.streamlit.app/


## Representation Analysis in Media (Gender & Race)
This one would be my preferred project!

I want to take the idea that “media representation matters” and actually try to measure it in a concrete way. Instead of just saying certain groups are underrepresented, I want to build a system that looks at datasets of movies and TV shows and tries to quantify how representation shows up; who appears, what kind of roles they get, and how prominent those roles are.

The main thing I’m interested in is whether disparities show up not just in raw counts, but in structure. For example, you might have decent representation in total numbers, but those same groups are mostly in minor or background roles. So I want to look at things like cast lists, role types, and billing order as rough proxies for importance, and turn that into measurable features.

### Execution Plan

By Week 5
- Collect dataset: Movie and TV metadata (cast lists, roles, genres)
- Build: Parsing and feature extraction pipeline
- Compute: Representation metrics (counts, proportions)

The focus is mostly on getting the data pipeline working. I’d collect a dataset of maybe 25 different movie/TV metadata (cast, roles, genres, release year), then build a parser that cleans and organizes everything. From there, I’d extract features like gender, role category (lead vs supporting if possible), and position in the cast list. The goal here is to define a basic set of metrics—counts, proportions, maybe a simple “prominence score” so I have a clear baseline for what representation looks like numerically and statistically.


By Week 7
- Add: Trend analysis over time
- Role-type comparisons (lead vs supporting), Intersectionality
- Justification: introduces deeper insight

I would add time as a dimension and compare different role types in respect to gender and race. Instead of just saying “X% of roles are female,” I can look at how that changes over time, or whether those roles are actually central to the story. I’d also explicitly compare lead vs supporting roles, since that feels like an important distinction that basic stats might miss. I will also take intersectionality into account.


Final
- Add: Visualization dashboard or report
- Deliverables: Analysis + reproducible pipeline

For the final version, I’d turn everything into something you can actually explore, like a small dashboard or interactive notebook. The idea is that you could filter by genre or year and see how the metrics change, instead of just reading a static summary. I also want the whole thing to be reproducible, so someone else could plug in a different dataset and get the same kind of analysis.


