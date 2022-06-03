# Adventure Game Mapper
## Python code for mapping text adventure games.

**Note:** This is still a work in progress! **Warning!** There are game spoilers to the game Zork II within the sample database included here.

This project arose because I discovered that the [Internet Archive](archive.org) has many old text adventure games, including those from Infocom (such as the Zork series, Planetfall, etc).

I can run these in dosbox on my Mac, but when I went looking for tools to help me map out such games, I found that they were all either obsolete, or couldn't run on a Mac. So I wrote this code in Python, which should run pretty well anywhere.

## Features
### Recording information on rooms and paths

![sample_main](https://user-images.githubusercontent.com/7020970/171783409-5a833a2c-d26d-4022-943b-09abfe3780fb.jpg)

The software requires the user to manually note the names of rooms as they are entered, and creating paths either to existing rooms or to a new room. It's also very useful to record for each room the obvious exits and any objects found there. This is pretty simple and quick. All information is stored in a sqlite database specific to the particular game you are working on.

### Show Map

![sample_map](https://user-images.githubusercontent.com/7020970/171783322-8fe929ac-8be5-4ee6-9c97-695ce308a391.jpg)

The mapping is a little clumsy because the connections in such games can be quite 'tangled', so the map shows only the nearest rooms to the one currently being explored. You can click on the name of a room to shift to a map centered on that room. Also because of the sometimes tangled nature of connections, I've colour-coded the directions and styled the dashes of the lines.

### Find Path

![sample_paths](https://user-images.githubusercontent.com/7020970/171783444-077083f9-e2e4-47b1-9341-cc4a77fe97e5.jpg)

This is an experimental feature to find the shortest path between two rooms. Sometimes it fails, but generally it will work, if not on the first try then the second. This can be great for finding a quick way to a room where you've left something. The 'Swap' button will allow you to generate the reverse journey.

### Search Rooms

![sample_search](https://user-images.githubusercontent.com/7020970/171783559-c7d6aaa8-2c6c-4c76-a4a0-b611c1227af4.jpg)

This generates a list of rooms in which the search text appears, either in the room name or its description. Great for reminding you of where you first found an object.


