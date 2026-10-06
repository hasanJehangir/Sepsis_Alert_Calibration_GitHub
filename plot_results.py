"""Plot the measured pilot endpoints, including the adverse sensitivity trade-off."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from experiment import binomial_ci

ROOT=Path(__file__).resolve().parent

def main():
    results=json.loads((ROOT/'results'/'pilot_results.json').read_text())
    rows=[r for r in results['results'] if r['site']=='B']
    assert [r['policy'] for r in rows]==['source_hourly','source_patient','target_patient']
    labels=['Source\nhourly','Source\npatient','Local\npatient']
    x=np.arange(3)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
                         'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(12,5.8),gridspec_kw={'width_ratios':[1,1.25]})
    colors=['#64748b','#0f766e','#2563eb']
    values=np.array([r['patient_false_alert_rate'] for r in rows])*100
    intervals=np.array([r['patient_false_alert_rate_ci95'] for r in rows])*100
    errors=np.vstack([values-intervals[:,0],intervals[:,1]-values])
    axes[0].bar(x,values,color=colors,width=.62,yerr=errors,capsize=5)
    axes[0].axhline(10,color='#b91c1c',linestyle='--',linewidth=1.2,label='10% patient target')
    for i,r in enumerate(rows):
        axes[0].text(i,intervals[i,1]+2,f"{values[i]:.1f}%\n{r['false_alerted_patients']}/1,136",
                     ha='center',va='bottom',fontsize=10)
    axes[0].set_ylim(0,60)
    axes[0].set_ylabel('Nonseptic patients with any alert (%)')
    axes[0].set_title('False alerts decline',loc='left',fontweight='bold',pad=14)
    axes[0].set_xticks(x,labels)
    axes[0].legend(loc='upper right',frameon=False,fontsize=9)
    values2=np.array([r['six_hour_window_sensitivity'] for r in rows])*100
    intervals2=np.array([r['sensitivity_ci95'] for r in rows])*100
    first=np.array([r['timely_first_alert_sensitivity'] for r in rows])*100
    firstci=np.array([binomial_ci(round(r['timely_first_alert_sensitivity']*r['septic_patients']),r['septic_patients']) for r in rows])*100
    axes[1].bar(x-.18,values2,width=.34,color='#0f766e',label='Any crossing in six-hour window',
                yerr=np.vstack([values2-intervals2[:,0],intervals2[:,1]-values2]),capsize=4)
    axes[1].bar(x+.18,first,width=.34,color='#d97706',label='First alert in six-hour window',
                yerr=np.vstack([first-firstci[:,0],firstci[:,1]-first]),capsize=4)
    for i,r in enumerate(rows):
        axes[1].text(i-.18,intervals2[i,1]+1.5,f"{values2[i]:.1f}%",ha='center',fontsize=10)
        axes[1].text(i+.18,firstci[i,1]+1.5,f"{first[i]:.1f}%",ha='center',fontsize=10)
    axes[1].set_ylim(0,115)
    axes[1].set_yticks(np.arange(0,101,20))
    axes[1].set_ylabel('Septic patients detected (%)')
    axes[1].set_title('Detection and first-alert timing remain weak',loc='left',fontweight='bold',pad=14)
    axes[1].set_xticks(x,labels)
    axes[1].legend(loc='upper right',frameon=False,fontsize=9)
    for ax in axes:
        ax.set_axisbelow(True)
        ax.yaxis.grid(alpha=.18)
    fig.suptitle('Hospital B • independent sepsis development pilot',x=.07,y=.98,ha='left',fontsize=17,fontweight='bold')
    fig.text(.07,.9,'1,176 eligible stays · 1,136 nonseptic · 40 septic · 95% exact binomial intervals',fontsize=11,color='#475569')
    fig.text(.07,.055,'Same hospital-A model for all policies. Hourly and patient calibration target different error events.\nPilot results only: no clinical benefit, guaranteed error control under shift, or publication readiness established.',fontsize=10,color='#475569')
    fig.subplots_adjust(left=.07,right=.98,bottom=.22,top=.78,wspace=.3)
    out=ROOT/'results'/'pilot_comparison.png'
    fig.savefig(out,dpi=200,bbox_inches='tight')
    plt.close(fig)
    print(out)

if __name__=='__main__':main()
