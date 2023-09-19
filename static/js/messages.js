let input_message = $('#input-message')
let message_body = $('.msg_card_body')
let send_message_form = $('#send-message-form')
const USER_ID = $('#logged-in-user').val()

let loc = window.location
let wsStart = 'wss://'

if(loc.protocol === 'https') {
    wsStart = 'wss://'
}
let id = '?'+USER_ID
let endpoint = wsStart + loc.host + loc.pathname+ id

const CHAT_NOTIFICATION_INTERVAL = 4000

var socket = new WebSocket(endpoint)


function getUnreadChatNotifications(){
  // print("get_read")
  if("{{request.user.is_authenticated}}"){
    socket.send(JSON.stringify({
      "command": "get_unread_chat_notifications",
      // "user":USER_ID
    }));
  }
}

function getAvailableThreads(){
  // print("get_read")
  if("{{request.user.is_authenticated}}"){
    socket.send(JSON.stringify({
      "command": "get_available_threads",
    }));
  }
}


socket.onopen = async function(e){
    console.log('open', e)
    // send_message_form.on('keyup' ,function (e){
    //   socket.send(JSON.stringify({
    //   'typing': 'true',
    //   }));
    // })
    send_message_form.on('submit', function (e){
        e.preventDefault()
        let message = input_message.val()
        let send_to = get_active_other_user_id()
        let thread_id = get_active_thread_id()

        let data = {
            'command':'message',
            'message': message,
            'sent_by': USER_ID,
            'send_to': send_to,
            'thread_id': thread_id
        }
        data = JSON.stringify(data)
        socket.send(data)
        $(this)[0].reset()
    })
//setInterval(getUnreadChatNotifications, CHAT_NOTIFICATION_INTERVAL)
//setInterval(getAvailableThreads, CHAT_NOTIFICATION_INTERVAL)
}

socket.onmessage = async function(e){
    console.log('message', e)
    let data = JSON.parse(e.data)
    let message = data['message']
    let sent_by_id = data['sent_by']
    let thread_id = data['thread_id']
    newMessage(message, sent_by_id, thread_id)
}

socket.onerror = async function(e){
    console.log('error', e)
}

socket.onclose = async function(e){
    console.log('close', e)
}

function newMessage(message, sent_by_id, thread_id) {
	if ($.trim(message) === '') {
		return false;
	}
	let message_element;
  var currentTime= new Date().toLocaleTimeString();
	let chat_id = 'chat_' + thread_id
	if(sent_by_id == USER_ID){
	    message_element = `
			<div class="d-flex mb-4 replied">
				<div class="msg_cotainer_send">
					${message}
					<span class="msg_time_send">${currentTime}</span>
				</div>
			</div>
	    `
    }
	else{
	    message_element = `
           <div class="d-flex mb-4 received">
              <div class="msg_cotainer">
                 ${message}
              <span class="msg_time">${currentTime}</span>
              </div>
           </div>
        `

    }

    let message_body = $('.messages-wrapper[chat-id="' + chat_id + '"] .msg_card_body')
	message_body.append($(message_element))
    message_body.animate({
        scrollTop: $(document).height()
    }, 100);
	input_message.val(null);
}


$('.contact-li').on('click', function (){
    $('.contacts .active').removeClass('active')
    $(this).addClass('active')

    // message wrappers
    let chat_id = $(this).attr('chat-id')
    $('.messages-wrapper.is_active').removeClass('is_active')
    $('.messages-wrapper[chat-id="' + chat_id +'"]').addClass('is_active')
    socket.send(JSON.stringify({
      "command": "mark_messages_read",
    }));
})


function get_active_other_user_id(){
    let other_user_id = $('.messages-wrapper.is_active').attr('other-user-id')
    other_user_id = $.trim(other_user_id)
    return other_user_id
}

function get_active_thread_id(){
    let chat_id = $('.messages-wrapper.is_active').attr('chat-id')
    let thread_id = chat_id.replace('chat_', '')
    return thread_id
}
