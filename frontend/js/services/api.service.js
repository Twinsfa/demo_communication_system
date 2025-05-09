import * as authApi from '../api/auth.js';
import * as notificationsApi from '../api/notifications.js';
import * as messagesApi from '../api/messages.js';
import * as formsApi from '../api/forms.js';
import * as evaluationsApi from '../api/evaluations.js';
import * as rewardsApi from '../api/rewards.js';

export default {
    ...authApi,
    ...notificationsApi,
    ...messagesApi,
    ...formsApi,
    ...evaluationsApi,
    ...rewardsApi,
}; 