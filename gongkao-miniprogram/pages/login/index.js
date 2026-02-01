var request = require('../../utils/request').request;
var wxLogin = require('../../utils/auth').wxLogin;
var saveLoginInfo = require('../../utils/auth').saveLoginInfo;
var checkLogin = require('../../utils/auth').checkLogin;

Page({
  data: {
    loading: false
  },

  onLoad: function() {
    console.log('登录页加载');
    // 检查是否已登录
    if (checkLogin()) {
      wx.switchTab({ url: '/pages/index/index' });
      return;
    }
  },

  handleLogin: function() {
    var that = this;
    if (that.data.loading) return;
    
    that.setData({ loading: true });
    console.log('开始登录流程');
    
    // 1. 获取微信登录code
    wxLogin().then(function(code) {
      console.log('获取code成功:', code);
      
      // 2. 调用后端登录接口
      return request({
        url: '/wx/login',
        method: 'POST',
        data: { code: code }
      });
    }).then(function(res) {
      console.log('登录API返回:', res);
      
      if (res.data.needBind) {
        // 需要绑定手机号
        var sessionKey = res.data.sessionKey || '';
        var openid = res.data.openid || '';
        wx.navigateTo({
          url: '/pages/bind-phone/index?sessionKey=' + sessionKey + '&openid=' + openid
        });
      } else {
        // 已绑定，保存登录信息
        saveLoginInfo(res.data.token, res.data.userInfo);
        
        wx.showToast({
          title: '登录成功',
          icon: 'success'
        });
        
        setTimeout(function() {
          wx.switchTab({ url: '/pages/index/index' });
        }, 1000);
      }
      that.setData({ loading: false });
    }).catch(function(err) {
      console.error('登录失败:', err);
      wx.showToast({
        title: err.message || '登录失败',
        icon: 'none'
      });
      that.setData({ loading: false });
    });
  }
});
