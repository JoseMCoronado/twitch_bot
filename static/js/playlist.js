setInterval(
  function()
  {
     $.getJSON(                            
        '/time',
        {},                                
        function(data)                     
        {
          $("#time").text(data);  
                                           
        });
     $.getJSON(                            
        '/currentsong',
        {},                                
        function(data)                     
        {
          $("#current-title").text(data.title);  
          $("#current-genre").text(data.genre);  
                                           
        });
     $.getJSON(                            
        '/playlist_table',
        {},                                
        function(data)                     
        {
        var c = [];
        c.push("<thead><th>Position</th><th>ID</th><th>Title</th><th>Genre</th><th>Duration</th><th>Time to Play</th><th>File</th></thead>")
        var time_till_play = 0  
        $.each(data, function(i, item) {             
            function str_pad_left(string,pad,length) {
                return (new Array(length+1).join(pad)+string).slice(-length);
            }

            var minutes = Math.floor(item.duration / 60);
            var seconds = item.duration - minutes * 60;
            var rminutes = Math.floor(time_till_play / 60);
            var rseconds = time_till_play - rminutes * 60;
            var rhours = Math.floor(time_till_play / 3600);

            var finalTime = str_pad_left(minutes,'0',2)+':'+str_pad_left(seconds,'0',2);
            var rFinalTime = str_pad_left(rhours,'0',2)+':'+str_pad_left(rminutes,'0',2)+':'+str_pad_left(rseconds,'0',2);
            c.push("<tr><td>" + item.pos + "</td>");
            c.push("<td>" + item.id + "</td>");
            c.push("<td>" + item.title + "</td>");
            c.push("<td>" + item.genre + "</td>");
            c.push("<td>" + finalTime + "</td>");
            c.push("<td>" + rFinalTime + "</td>");
            c.push("<td>" + item.file + "</td></tr>");               
            time_till_play += parseFloat(item.duration)
        });

        $('#playlist_table').html(c.join(""));
        });
  },
  1000);                                    