var checkLogin = require('../../utils/auth').checkLogin;
var clearLoginInfo = require('../../utils/auth').clearLoginInfo;
var request = require('../../utils/request').request;

Page({
  data: {
    loading: true,
    userInfo: null,
    menuList: [
      { icon: 'calendar-o', title: '打卡日历', url: '/pages/checkin/index' },
      { icon: 'bell-o', title: '消息提醒设置', action: 'subscribe' },
      { icon: 'records', title: '学习记录', url: '' },
      { icon: 'todo-list-o', title: '我的作业', url: '' },
      { icon: 'comment-o', title: '督学消息', url: '/pages/messages/index' },
      { icon: 'question-o', title: '常见问题', url: '' },
      { icon: 'service-o', title: '联系客服', url: '' },
      { icon: 'setting-o', title: '设置', url: '' }
    ]
  },

  onShow: function() {
    console.log('我的页面显示');
    if (!checkLogin()) {
      this.setData({ loading: false, userInfo: null });
      return;
    }
    this.loadUserInfo();
  },

  loadUserInfo: function() {
    var that = this;
    request({ url: '/students/me' }).then(function(res) {
      console.log('我的-用户信息:', res.data);
      that.setData({
        userInfo: res.data,
        loading: false
      });
    }).catch(function(err) {
      console.error('获取用户信息失败:', err);
      that.setData({ loading: false });
    });
  },

  handleLogin: function() {
    wx.navigateTo({ url: '/pages/login/index' });
  },

  handleMenuTap: function(e) {
    var url = e.currentTarget.dataset.url;
    var action = e.currentTarget.dataset.action;
    
    if (action === 'subscribe') {
      this.handleSubscribe();
    } else if (url) {
      wx.navigateTo({ url: url });
    } else {
      wx.showToast({ title: '功能开发中', icon: 'none' });
    }
  },

  handleSubscribe: function() {
    var that = this;
    
    // 检查是否登录
    if (!checkLogin()) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }
    
    // 先获取模板列表
    request({ url: '/wx/subscribe-templates' }).then(function(res) {
      console.log('订阅模板列表:', res.data);
      var templates = res.data.templates || [];
      
      if (templates.length === 0) {
        wx.showModal({
          title: '提示',
          content: '暂无可用的订阅消息模板，请联系管理员配置',
          showCancel: false
        });
        return;
      }
      
      // 提取模板ID列表
      var tmplIds = templates.map(function(t) {
        return t.templateId;
      });
      
      console.log('请求订阅授权，模板ID:', tmplIds);
      
      // 请求订阅消息授权
      wx.requestSubscribeMessage({
        tmplIds: tmplIds,
        success: function(subscribeRes) {
          console.log('订阅结果:', subscribeRes);
          
          var accepted = [];
          var rejected = [];
          
          for (var key in subscribeRes) {
            if (subscribeRes[key] === 'accept') {
              accepted.push(key);
            } else if (subscribeRes[key] === 'reject') {
              rejected.push(key);
            }
          }
          
          if (accepted.length > 0) {
            wx.showModal({
              title: '订阅成功',
              content: '已成功订阅' + accepted.length + '个消息，我们将在合适的时候向您推送重要提醒。',
              showCancel: false
            });
          } else if (rejected.length > 0) {
            wx.showModal({
              title: '提示',
              content: '您拒绝了消息订阅，将无法收到课程、作业等重要提醒。可随时在"我的-消息提醒设置"中重新订阅。',
              showCancel: false
            });
          } else {
            wx.showToast({
              title: '未做任何更改',
              icon: 'none'
            });
          }
        },
        fail: function(err) {
          console.error('订阅失败:', err);
          wx.showToast({
            title: '订阅失败，请重试',
            icon: 'none'
          });
        }
      });
    }).catch(function(err) {
      console.error('获取模板列表失败:', err);
      wx.showToast({
        title: '加载失败，请重试',
        icon: 'none'
      });
    });
  },

  handleLogout: function() {
    var that = this;
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: function(res) {
        if (res.confirm) {
          clearLoginInfo();
          that.setData({ userInfo: null });
          wx.showToast({ title: '已退出', icon: 'success' });
        }
      }
    });
  }
});
