export const ONBOARDING_COMPLETED_KEY = 'onboarding_completed';
export const ONBOARDING_STEP_KEY = 'onboarding_step';

export type OnboardingStep = 'welcome' | 'first_action' | 'complete';

export function readOnboardingCompleted(): boolean {
  if (typeof window === 'undefined') return false;
  return window.localStorage.getItem(ONBOARDING_COMPLETED_KEY) === 'true';
}

export function readOnboardingStep(): OnboardingStep {
  if (typeof window === 'undefined') return 'welcome';
  const step = window.localStorage.getItem(ONBOARDING_STEP_KEY);
  if (step === 'first_action' || step === 'complete' || step === 'welcome') return step;
  return 'welcome';
}

export function writeOnboardingStep(step: OnboardingStep) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(ONBOARDING_STEP_KEY, step);
}

export function writeOnboardingCompleted() {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(ONBOARDING_COMPLETED_KEY, 'true');
  window.localStorage.setItem(ONBOARDING_STEP_KEY, 'complete');
}
