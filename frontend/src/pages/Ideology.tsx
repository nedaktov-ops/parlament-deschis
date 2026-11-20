import { useTranslation } from "react-i18next";

export default function Ideology() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <section className="py-2" data-enter>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
          {t("view.ideology.title", "Ideological spatial map")}
        </h1>
        <p className="mt-2 text-sm sm:text-base text-slate-400 max-w-3xl">
          {t("view.ideology.intro", "Ideological positioning of parties (left-right, authoritarian-libertarian) based on CHES and PopuList data.")}
        </p>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <div className="text-slate-500 text-sm py-12 text-center">
          {t("empty.ideology", "Ideological data not yet available.")}
        </div>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <h2 className="text-lg font-semibold text-slate-100 mb-3">
          {t("view.ideology.note", "Ideological data not yet ingested. No figures or invented axes shown.")}
        </h2>
        <ul className="text-sm text-slate-400 space-y-2 max-w-md">
          <li>
            {t("view.ideology.sources", "Planned sources:")}{" "}
            <span className="text-slate-300">CHES (Chapel Hill Expert Survey), PopuList, Party Facts</span>
          </li>
          <li>
            {t("view.ideology.licence", "Licence-gated:")}{" "}
            <span className="text-slate-300">
              CC0 / CC BY 4.0 / OGL-ROU-1.0 sources only; CC BY-SA / CC BY-NC treated as cross-check only
            </span>
          </li>
          <li>
            {t("view.ideology.status", "Status:")}{" "}
            <span className="text-slate-300">Not ingested — no figures published</span>
          </li>
        </ul>
      </section>
    </div>
  );
}
