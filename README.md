# adventure_games_mapper
Python code for mapping text adventure games.

This arose because I discovered that archive.org has many old text adventure games, including those from Infocom (such as the Zork series, Planetfall, etc).

I can run these in dosbox on my Mac, but when I went looking for tools to help me map out such games, I found that they were either obsolete, or couldn't run on a Mac. So I wrote this code in Python, which should run pretty well anywhere.

The mapping is a little clumsy because the connections in such games can be quite 'tangled', so the map shows only the nearest rooms to the one currently being explored. You can click on the name of a room to shift to a map centered on that room. Also because of the sometimes tangled nature of connections, I've colour-coded the directions.

![sample_map](https://user-images.githubusercontent.com/7020970/170919775-c40af6c2-e3ba-4435-ba16-c351759ac6e2.jpg)

There's also an experimental feature to find the shortest path between two rooms.

This is still a work in progress. Warning! There are spoilers in the sample zork2 database included here.
