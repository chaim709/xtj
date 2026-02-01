var checkLogin = require('../../utils/auth').checkLogin;
var clearLoginInfo = require('../../utils/auth').clearLoginInfo;
var request = require('../../utils/request').request;

Page({
  data: {
    loading: true,
    userInfo: null,
    menuList: [
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
    this.setData({ loading: false });
    // 暂时不调用API
    // if (!checkLogin()) {
    //   this.setData({ loading: false });
    //   return;
    // }
    // this.loadUserInfo();
  },

  loadUserInfo: function() {
    var that = this;
    request({ url: '/students/me' }).then(function(res) {
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
    if (url) {
      wx.navigateTo({ url: url });
    } else {
      wx.showToast({ title: '功能开发中', icon: 'none' });
    }
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
