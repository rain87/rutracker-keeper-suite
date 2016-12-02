use rutracker_torrents_stats;

function print_stat(record) {
  print(record.ts);
  for(var forum in record.forums) {
    print(forum);
    forum = record.forums[forum];
    for(var peersType in forum) {
        var peers = forum[peersType];
        print(peersType + ':s0=' + peers.s0.length + ':s1=' + peers.s1.length + ':s2=' + peers.s2.length + ':s3m=' + peers.s3m.length);
    }
  }
}

db.stat.find().map(function(rec) { print_stat(rec); }).reduce(function(s) { return undefined; });
