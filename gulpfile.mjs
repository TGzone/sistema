import gulp from 'gulp';
import open from 'gulp-open';

// Sua tarefa original
gulp.task('open-app', function(){
  return gulp.src('pages/dashboard.html')
  .pipe(open());
});

// NOVA LINHA: Define a tarefa padrão que o Netlify procura
gulp.task('default', gulp.series('open-app'));