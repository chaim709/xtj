var request = require('../../utils/request').request;
var checkLogin = require('../../utils/auth').checkLogin;

Page({
  data: {
    loading: true,
    loadingMore: false,
    messages: [],
    page: 1,
    limit: 20,
    hasMore: true,
    total: 0
  },

  onShow: function() {
    if (!checkLogin()) {
      wx.navigateTo({ url: '/pages/login/index' });
      return;
    }
    this.loadMessages(true);
  },

  onPullDownRefresh: function() {
    var that = this;
    that.loadMessages(true);
    setTimeout(function() {
      wx.stopPullDownRefresh();
    }, 1500);
  },

  onReachBottom: function() {
    if (this.data.hasMore && !this.data.loadingMore) {
      this.loadMessages(false);
    }
  },

  loadMessages: function(reset) {
    var that = this;
    
    if (reset) {
      that.setData({
        page: 1,
        messages: [],
        hasMore: true,
        loading: true
      });
    } else {
      that.setData({ loadingMore: true });
    }

    request({
      url: '/students/me/messages',
      data: {
        page: that.data.page,
        limit: that.data.limit
      }
    }).then(function(res) {
      console.log('消息数据:', res.data);
      
      var newMessages = res.data.items || [];
      var total = res.data.total || 0;
      
      var allMessages = reset ? newMessages : that.data.messages.concat(newMessages);
      
      that.setData({
        messages: allMessages,
        total: total,
        hasMore: allMessages.length < total,
        page: that.data.page + 1,
        loading: false,
        loadingMore: false
      });
    }).catch(function(err) {
      console.error('获取消息失败:', err);
      wx.showToast({ title: '获取失败', icon: 'none' });
      that.setData({ loading: false, loadingMore: false });
    });
  },

  viewDetail: function(e) {
    var message = e.currentTarget.dataset.item;
    console.log('查看消息详情:', message);
    wx.showModal({
      title: message.title,
      content: message.fullContent || message.content || '暂无内容',
      showCancel: false,
      confirmText: '知道了'
    });
  }
});
