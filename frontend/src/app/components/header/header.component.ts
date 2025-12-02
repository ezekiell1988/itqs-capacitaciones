import { Component, Input } from '@angular/core';
import { IonHeader, IonToolbar, IonTitle, IonButtons } from '@ionic/angular/standalone';

@Component({
  selector: 'app-header',
  template: `
    <ion-header>
      <ion-toolbar color="primary">
        <ion-title>{{ title }}</ion-title>
        <ion-buttons slot="end">
          <ng-content></ng-content>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
  `,
  standalone: true,
  imports: [IonHeader, IonToolbar, IonTitle, IonButtons]
})
export class HeaderComponent {
  @Input() title: string = 'ITQS Capacitaciones';
}
