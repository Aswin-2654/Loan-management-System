import { useEffect, useRef, useState } from "react";

type Props = {
  variant: "loading" | "success";
  title: string;
  subtitle?: string;
  onClose?: () => void;
};

export default function CashfreePaymentOverlay({ variant, title, subtitle, onClose }: Props) {
  const LOADING_SWITCH_MS = 1400;
  const SUCCESS_AUTO_CLOSE_MS = 3200;
  const [loadingPhase, setLoadingPhase] = useState<"processing" | "cashfree">("processing");
  const onCloseRef = useRef<typeof onClose>(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (variant !== "loading") return;
    setLoadingPhase("processing");
    const timer = window.setTimeout(() => setLoadingPhase("cashfree"), LOADING_SWITCH_MS);
    return () => window.clearTimeout(timer);
  }, [variant]);

  useEffect(() => {
    if (variant !== "success") return;
    const timer = window.setTimeout(() => onCloseRef.current?.(), SUCCESS_AUTO_CLOSE_MS);
    return () => window.clearTimeout(timer);
  }, [variant]);

  const loadingTitle = loadingPhase === "processing" ? "Processing payment" : "Moving to Cashfree";
  const loadingSubtitle =
    loadingPhase === "processing" ? "Verifying transaction..." : "Redirecting to secure Cashfree checkout...";
  const successTitle = title || "Successful amount credited";
  const successSubtitle = subtitle || "Amount credited to wallet.";

  return (
    <div
      style={styles.overlay}
      role="status"
      aria-live="polite"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onCloseRef.current?.();
      }}
    >
      <style>{keyframes}</style>
      <div style={styles.card} onMouseDown={(e) => e.stopPropagation()}>
        {variant === "loading" ? (
          <>
            <div style={styles.title}>{loadingTitle}</div>
            <div style={styles.subtitle}>{loadingSubtitle}</div>
            <div style={styles.loadingTrack} aria-hidden>
              <div style={styles.loadingShimmer} />
              <div style={styles.loadingFill} />
              <div style={styles.loadingCoin}>
                <span style={styles.loadingCoinText}>{"\u20B9"}</span>
              </div>
            </div>
            <div style={styles.phaseRow} aria-hidden>
              <span style={loadingPhase === "processing" ? styles.phaseActive : styles.phaseIdle}>Processing</span>
              <span style={styles.phaseSep}>{"->"}</span>
              <span style={loadingPhase === "cashfree" ? styles.phaseActive : styles.phaseIdle}>Cashfree</span>
            </div>
          </>
        ) : (
          <>
            <div style={styles.title}>{successTitle}</div>
            <div style={styles.subtitle}>{successSubtitle}</div>
            <div style={styles.transferScene} aria-hidden>
              <div style={styles.bankNode}>
                <div style={styles.nodeIcon}>Bank</div>
              </div>
              <div style={styles.walletNode}>
                <div style={styles.nodeIcon}>Wallet</div>
              </div>
              <div style={styles.transferCoin}>
                <span style={styles.transferCoinText}>{"\u20B9"}</span>
              </div>
              <div style={styles.transferBeam} />
            </div>
            <div style={styles.successLine}>Successful amount credited.</div>
          </>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, any> = {
  overlay: {
    position: "fixed",
    inset: 0,
    display: "grid",
    placeItems: "center",
    background: "rgba(24, 15, 9, 0.96)",
    zIndex: 14000,
    pointerEvents: "auto",
  },
  card: {
    pointerEvents: "auto",
    width: "min(460px, 92vw)",
    minHeight: 250,
    borderRadius: 18,
    padding: "22px 20px",
    background: "linear-gradient(180deg, #fefaf4, #f8ecd8)",
    border: "1px solid #d6b792",
    boxShadow: "0 26px 72px rgba(0, 0, 0, 0.42)",
    display: "grid",
    gap: 12,
    alignContent: "start",
  },
  title: {
    fontSize: 21,
    fontWeight: 900,
    color: "#4b2f1d",
    textAlign: "center",
    lineHeight: 1.2,
  },
  subtitle: {
    fontSize: 14,
    fontWeight: 700,
    color: "#7b5132",
    textAlign: "center",
    lineHeight: 1.3,
  },
  loadingTrack: {
    position: "relative",
    height: 36,
    borderRadius: 999,
    background: "#cfae87",
    border: "1px solid #ab8258",
    overflow: "hidden",
    marginTop: 8,
  },
  loadingShimmer: {
    position: "absolute",
    inset: 0,
    background: "linear-gradient(100deg, rgba(255,255,255,0), rgba(255,255,255,0.26), rgba(255,255,255,0))",
    animation: "cf-track-shimmer 1200ms ease-in-out infinite",
  },
  loadingFill: {
    position: "absolute",
    inset: 0,
    width: "35%",
    background: "linear-gradient(90deg, rgba(59,130,246,0.18), rgba(37,99,235,0.85), rgba(59,130,246,0.18))",
    animation: "cf-track-fill 1600ms ease-in-out infinite",
    borderRadius: 999,
  },
  loadingCoin: {
    position: "absolute",
    top: 3,
    left: "6%",
    width: 30,
    height: 30,
    borderRadius: 999,
    background: "radial-gradient(circle at 32% 32%, #ffe8a6, #d99c2b 66%, #915f1c)",
    border: "1px solid rgba(96, 58, 20, 0.5)",
    display: "grid",
    placeItems: "center",
    animation: "cf-rupee-run 1600ms ease-in-out infinite",
    transformStyle: "preserve-3d",
  },
  loadingCoinText: {
    fontSize: 12,
    fontWeight: 900,
    color: "#4e2e13",
  },
  phaseRow: {
    display: "flex",
    justifyContent: "center",
    gap: 8,
    alignItems: "center",
    marginTop: 2,
  },
  phaseActive: {
    fontSize: 13,
    fontWeight: 900,
    color: "#5f3518",
  },
  phaseIdle: {
    fontSize: 13,
    fontWeight: 800,
    color: "#9b7a5b",
  },
  phaseSep: {
    color: "#8b6848",
    fontWeight: 900,
  },
  transferScene: {
    position: "relative",
    height: 130,
    marginTop: 8,
  },
  bankNode: {
    position: "absolute",
    left: 4,
    top: 36,
    width: 88,
    height: 72,
    borderRadius: 12,
    background: "#b98b5d",
    border: "1px solid #855c35",
    display: "grid",
    placeItems: "center",
  },
  walletNode: {
    position: "absolute",
    right: 4,
    top: 36,
    width: 88,
    height: 72,
    borderRadius: 12,
    background: "#8f643f",
    border: "1px solid #684522",
    display: "grid",
    placeItems: "center",
  },
  nodeIcon: {
    color: "#fff5ea",
    fontSize: 13,
    fontWeight: 900,
    letterSpacing: "0.01em",
  },
  transferBeam: {
    position: "absolute",
    left: 90,
    right: 90,
    top: 70,
    height: 4,
    borderRadius: 999,
    background: "linear-gradient(90deg, #9d6c3c, #d3a06d, #9d6c3c)",
    opacity: 0.65,
  },
  transferCoin: {
    position: "absolute",
    top: 56,
    left: "18%",
    width: 30,
    height: 30,
    borderRadius: 999,
    background: "radial-gradient(circle at 32% 32%, #ffe8a6, #d99c2b 66%, #915f1c)",
    border: "1px solid rgba(96, 58, 20, 0.5)",
    display: "grid",
    placeItems: "center",
    animation: "cf-bank-wallet-coin 2200ms cubic-bezier(.2,.9,.2,1) forwards",
    transformStyle: "preserve-3d",
  },
  transferCoinText: {
    fontSize: 12,
    fontWeight: 900,
    color: "#4e2e13",
  },
  successLine: {
    textAlign: "center",
    fontSize: 14,
    fontWeight: 900,
    color: "#5c3920",
    marginTop: 2,
  },
};

const keyframes = `
@keyframes cf-track-shimmer {
  0% { transform: translateX(-80%) }
  100% { transform: translateX(80%) }
}
@keyframes cf-rupee-run {
  0% { left: 6%; transform: translateX(0) rotateY(0deg) }
  50% { left: 94%; transform: translateX(-100%) rotateY(360deg) }
  100% { left: 6%; transform: translateX(0) rotateY(720deg) }
}
@keyframes cf-track-fill {
  0% { transform: translateX(-55%); opacity: 0.72 }
  50% { transform: translateX(120%); opacity: 0.9 }
  100% { transform: translateX(-55%); opacity: 0.72 }
}
@keyframes cf-bank-wallet-coin {
  0% { left: 18%; transform: rotateY(0deg) }
  65% { left: 82%; transform: rotateY(720deg) }
  100% { left: 82%; transform: rotateY(1080deg) }
}
`;
