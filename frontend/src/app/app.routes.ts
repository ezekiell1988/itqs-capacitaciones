import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'home',
    loadComponent: () => import('./home/home.page').then((m) => m.HomePage),
  },
  {
    path: 'test',
    loadComponent: () => import('./test/test.page').then((m) => m.TestPage),
  },
  {
    path: 'report',
    loadComponent: () => import('./report/report.page').then((m) => m.ReportPage),
  },
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full',
  },
];
