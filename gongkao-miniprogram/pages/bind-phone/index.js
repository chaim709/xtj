var request = require('../../utils/request').request;
var saveLoginInfo = require('../../utils/auth').saveLoginInfo;

Page({
  data: {
    sessionKey: '',
    openid: '',
    loading: false,
    devMode: true,
    inputPhone: ''
  },

  onLoad: function(options) {
    console.log('绑定页面加载', options);
    this.setData({
      sessionKey: options.sessionKey || '',
      openid: options.openid || ''
    });
  },

  onPhoneInput: function(e) {
    var value = e.detail.value || e.detail || '';
    console.log('输入手机号:', value);
    this.setData({ inputPhone: value });
  },

  handleDevBind: function() {
    var that = this;
    var phone = (that.data.inputPhone || '').trim();
    
    console.log('准备绑定手机号:', phone);
    
    if (!phone || phone.length !== 11) {
      wx.showToast({
        title: '请输入11位手机号',
        icon: 'none'
      });
      return;
    }
    
    that.bindPhone({ phone: phone });
  },

  bindPhone: function(phoneData) {
    var that = this;
    if (that.data.loading) return;
    
    that.setData({ loading: true });
    console.log('开始绑定:', phoneData);

    request({
      url: '/wx/bind-phone',
      method: 'POST',
      data: {
        openid: that.data.openid,
        sessionKey: that.data.sessionKey,
        phone: phoneData.phone
      }
    }).then(function(res) {
      console.log('绑定返回:', res);
      
      if (res.success) {
        saveLoginInfo(res.data.token, res.data.userInfo);
        
        wx.showToast({
          title: '绑定成功',
          icon: 'success'
        });

        setTimeout(function() {
          wx.switchTab({ url: '/pages/index/index' });
        }, 1000);
      }
      that.setData({ loading: false });
    }).catch(function(err) {
      console.error('绑定失败:', err);
      wx.showToast({
        title: err.message || '绑定失败',
        icon: 'none'
      });
      that.setData({ loading: false });
    });
  }
});
