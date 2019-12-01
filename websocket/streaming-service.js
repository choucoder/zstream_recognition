function createStreamingWebSocket( address, name, topic ) {
    ws = new WebSocket(address)
    wsName = name

    ws.onopen = function( e ) {
        console.log("Opened.")
        request = {'topic': topic, 'signal': 0}
        request = JSON.stringify(request)
        ws.send(request)
    }

    ws.onmessage = function( msg ) {
        msg = JSON.parse(msg.data)
        frame = msg.data
        image = document.getElementById('video-view')
        src = "data:image/jpg;base64," + frame

        if ( msg.online ) {
            if ( msg.type == 0 && msg.status == 201 ) {
                image.src = src
            }
        }
    }

    ws.onerror = function( e ) {
        console.log("Error: " + e)
    }

    ws.onclose = function( e ) {
        if ( e.target == ws ) {
            ws.close()
            console.log("Disconnect.")
        }
    }
}