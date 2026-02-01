var request = require('../../utils/request').request;
var checkLogin = require('../../utils/auth').checkLogin;
var getUserInfo = require('../../utils/auth').getUserInfo;

Page({
  data: {
    conversationId: '',
    messages: [],
    inputText: '',
    sending: false,
    userInfo: null
  },

  onLoad: function() {
    var userInfo = getUserInfo();
    this.setData({ userInfo: userInfo });
    
    // 添加欢迎消息
    this.addMessage('assistant', '你好！我是你的智能督学助手，有什么可以帮助你的吗？');
  },

  onShow: function() {
    if (!checkLogin()) {
      wx.navigateTo({ url: '/pages/login/index' });
      return;
    }
  },

  onInputChange: function(e) {
    this.setData({ inputText: e.detail.value || '' });
  },

  sendMessage: function() {
    var that = this;
    var text = (that.data.inputText || '').trim();
    
    if (!text) {
      wx.showToast({ title: '请输入消息', icon: 'none' });
      return;
    }
    
    if (that.data.sending) return;
    
    // 添加用户消息
    that.addMessage('user', text);
    that.setData({ 
      inputText: '',
      sending: true
    });
    
    // 调用后端API
    request({
      url: '/coze/chat',
      method: 'POST',
      data: {
        message: text,
        conversation_id: that.data.conversationId
      }
    }).then(function(res) {
      console.log('扣子回复:', res.data);
      
      that.addMessage('assistant', res.data.reply);
      that.setData({
        conversationId: res.data.conversationId || that.data.conversationId,
        sending: false
      });
      
      // 滚动到底部
      that.scrollToBottom();
    }).catch(function(err) {
      console.error('发送失败:', err);
      that.addMessage('assistant', '抱歉，我暂时无法回复，请稍后再试。');
      that.setData({ sending: false });
    });
  },

  addMessage: function(role, content) {
    var messages = this.data.messages;
    messages.push({
      id: Date.now(),
      role: role,
      content: content,
      time: this.formatTime(new Date())
    });
    this.setData({ messages: messages });
  },

  formatTime: function(date) {
    var h = date.getHours();
    var m = date.getMinutes();
    return (h < 10 ? '0' + h : h) + ':' + (m < 10 ? '0' + m : m);
  },

  scrollToBottom: function() {
    wx.pageScrollTo({
      scrollTop: 999999,
      duration: 300
    });
  }
});
