This is project which I decided to tackle after toying around with BitTorrent for awhile. It's a second iteration where I tried to make it a bit tidier and extensible using preferably only the Python standard lib. In the end I needed to use external libraries, to mention:
- `aiohttp` to support concurrent HTTP requests
- `bitarray`to support fast and light bitarray implementations in C

Currently supported features:
[x] - HTTP Trackers
[x] - Single file torrents
[ ] - Multi file torrents
[ ] - UDP Trackers
[ ] - Seeding

I will hopefully work on UDP Trackers and seeding, as it isn't super complex to be added, multi file torrents might require a bit more work however.

For UDP Trackers the great deal is finding a concurrent library capable of doing DNS queries and async UDP sockets aswel, which might aswell be built from the ground up given it might be easier than finding something adequate.

I wrote a blog post for the project [here](https://gazev.com/bittorrent)