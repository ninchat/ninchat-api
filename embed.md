Examples on how to embed Ninchat to a web page. There are two different use cases for embedding:

1. Queued 1-on-1 customer service chat
2. Multiple user chat room(s)


Loading and initialization
==========================

You can load Ninchat to an existing block level element on the page (usually the chat room) or let the script create a floating element to bottom right corner of the screen (customer service). You will need to create an initialization function called `NinchatAsyncInit` and include the required JavaScript file which will call the said function after loading.


Customer service example
------------------------

Load the JavaScript and asynchronously initialize a chat bar to bottom right:

    <script type="text/javascript">
        window.NinchatAsyncInit = function() {
            window.Ninchat.embedInit({
        		audienceRealmId: 'YOUR_REALM_ID',
		        titleText: 'Customer service',
		        motd: 'Welcome to <strong>ACME</strong> customer service'
	        });
        };

        (function(doc) {
	        if (doc.getElementById('ninchat-js')) {
		        return;
	        }

	        var js, first = doc.getElementsByTagName('script')[0];

            js     = doc.createElement('script');
	        js.id  = 'ninchat-js';
            js.src = 'https://ninchat.com/ng/js/embed.js';
            first.parentNode.insertBefore(js, first);
        }(document));
    </script>


Chat room example
-----------------

Load the JavaScript and add the chat room to pre-defined element on page:

    <div id="ninchat-chatroom" style="width: 300px; height: 400px;"></div>
    
    <script type="text/javascript">
        window.NinchatAsyncInit = function() {
            window.Ninchat.embedInit({
                channelId: 'YOUR_CHANNEL_ID',
        		containerId: 'ninchat-chatroom'
	        });
        };

        (function(doc) {
	        if (doc.getElementById('ninchat-js')) {
		        return;
	        }

	        var js, first = doc.getElementsByTagName('script')[0];

            js     = doc.createElement('script');
	        js.id  = 'ninchat-js';
            js.src = 'https://ninchat.com/ng/js/embed.js';
            first.parentNode.insertBefore(js, first);
        }(document));
    </script>


Multiple chat rooms example
---------------------------

Show two different chat rooms, e.g. one where only experts are allowed to talk and guests can follow the discussion and another where guests are allowed to talk:

    <div id="ninchat-experts" style="width: 300px; height: 400px; float: left;"></div>
    <div id="ninchat-guests" style="width: 300px; height: 400px; float: left;"></div>
    
    <script type="text/javascript">
        window.NinchatAsyncInit = function() {
            window.Ninchat.embedInit({
                channelId: 'YOUR_EXPERT_CHANNEL_ID',
        		containerId: 'ninchat-experts',
        		hideCommand: true,
        		remember: false
	        });
            window.Ninchat.embedInit({
                channelId: 'YOUR_GUEST_CHANNEL_ID',
        		containerId: 'ninchat-guests'
	        });
        };

        (function(doc) {
	        if (doc.getElementById('ninchat-js')) {
		        return;
	        }

	        var js, first = doc.getElementsByTagName('script')[0];

            js     = doc.createElement('script');
	        js.id  = 'ninchat-js';
            js.src = 'https://ninchat.com/ng/js/embed.js';
            first.parentNode.insertBefore(js, first);
        }(document));
    </script>



Initialization parameters
-------------------------


Public API
----------


