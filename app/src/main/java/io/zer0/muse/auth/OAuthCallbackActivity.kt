package io.zer0.muse.auth

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import io.zer0.common.Logger

/**
 * P1-6: OAuth 回调空 Activity — 仅用于接收 `io.zer0.muse://oauth/callback` Deep Link。
 *
 * 工作流程:
 *  1. 浏览器完成 Authorization Code Flow 授权后,跳转到 redirectUri
 *     (`io.zer0.muse://oauth/callback?code=xxx&state=yyy`)
 *  2. 系统匹配到本 Activity 的 intent-filter,启动本 Activity
 *  3. [onCreate] / [onNewIntent] 解析 query 中的 code + state,
 *     调用 [OAuthManager.completeAuthorizationCodeFlow] 完成 Flow
 *  4. 立即 [finish],用户看到的是浏览器关闭后回到 ProviderEditPage
 *
 * 注意:
 *  - 本 Activity 无 UI(setTheme 透明),仅做转发
 *  - exported="true" 是 Deep Link 必需的(浏览器 → 应用跳转)
 *  - state 校验由 [OAuthManager.completeAuthorizationCodeFlow] 内部完成(CSRF 防护)
 */
class OAuthCallbackActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        handleIntent(intent)
        finish()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIntent(intent)
        finish()
    }

    /** 从 Intent 解析 code + state,转发给 [OAuthManager]。 */
    private fun handleIntent(intent: Intent?) {
        val data: Uri = intent?.data ?: run {
            Logger.w(TAG, "OAuthCallbackActivity 收到空 data,忽略")
            return
        }
        // Explicit intents bypass Android's intent-filter matching; validate here too.
        if (data.scheme != "io.zer0.muse" || data.host != "oauth" || data.path != "/callback") {
            Logger.w(TAG, "OAuth 回调 URI 不匹配,忽略")
            return
        }
        val code = data.getQueryParameter("code").orEmpty()
        val state = data.getQueryParameter("state").orEmpty()
        // Never log the URI, authorization code, state or provider-supplied description.
        val error = data.getQueryParameter("error")
        if (!error.isNullOrBlank()) {
            if (!OAuthManager.rejectAuthorizationCodeFlow(state)) {
                Logger.w(TAG, "OAuth 错误回调未通过 state 校验,忽略")
            }
            return
        }
        if (code.isBlank() || state.isBlank()) {
            Logger.w(TAG, "OAuth 回调缺 code/state,忽略")
            return
        }
        OAuthManager.completeAuthorizationCodeFlow(code, state)
    }

    private companion object {
        private const val TAG = "OAuthCallbackActivity"
    }
}
