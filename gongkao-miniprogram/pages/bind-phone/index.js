const { request } = require('../../utils/request');
const { saveLoginInfo } = require('../../utils/auth');

Page({
  data: {
    sessionKey: '',
    openid: '',
    loading: false,
    devMode: true,  // 开发模式
    inputPhone: ''
  },

  onLoad(options) {
    this.setData({
      sessionKey: options.sessionKey || '',
      openid: options.openid || ''
    });
  },

  // 获取手机号（微信授权方式）
  async getPhoneNumber(e) {
    if (e.detail.errMsg !== 'getPhoneNumber:ok') {
      wx.showToast({
        title: '需要授权手机号才能使用',
        icon: 'none'
      });
      return;
    }

    const { encryptedData, iv } = e.detail;
    await this.bindPhone({
      encryptedData,
      iv
    });
  },

  // 开发模式：手动输入手机号
  onPhoneInput(e) {
    this.setData({ inputPhone: e.detail.value });
  },

  async handleDevBind() {
    const phone = this.data.inputPhone.trim();
    if (!phone || phone.length !== 11) {
      wx.showToast({
        title: '请输入正确的手机号',
        icon: 'none'
      });
      return;
    }
    await this.bindPhone({ phone });
  },

  // 绑定手机号
  async bindPhone(phoneData) {
    if (this.data.loading) return;
    
    this.setData({ loading: true });

    try {
      const res = await request({
        url: '/wx/bind-phone',
        method: 'POST',
        data: {
          openid: this.data.openid,
          sessionKey: this.data.sessionKey,
          ...phoneData
        }
      });

      if (res.success) {
        saveLoginInfo(res.data.token, res.data.userInfo);
        
        wx.showToast({
          title: '绑定成功',
          icon: 'success'
        });

        setTimeout(() => {
          wx.switchTab({ url: '/pages/index/index' });
        }, 1000);
      }
    } catch (err) {
      console.error('绑定失败:', err);
      wx.showToast({
        title: err.message || '绑定失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  }
});
